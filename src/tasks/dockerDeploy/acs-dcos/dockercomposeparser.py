import hashlib
import logging
import math
import os

import yaml

import acsclient
import acsinfo
import dockerregistry
import marathon
import portmappings
import serviceparser


class DockerComposeParser(object):
    def __init__(self, compose_file, master_url, acs_host, acs_port, acs_username,
                 acs_password, acs_private_key, group_name, group_qualifier, group_version,
                 registry_host, registry_username, registry_password,
                 minimum_health_capacity):

        self._ensure_docker_compose(compose_file)
        with open(compose_file, 'r') as compose_stream:
            self.compose_data = yaml.load(compose_stream)

        self.acs_info = acsinfo.AcsInfo(acs_host, acs_port, acs_username,
                                        acs_password, acs_private_key, master_url)

        self.group_name = group_name
        self.group_qualifier = group_qualifier
        self.group_version = group_version

        self.registry_host = registry_host
        self.registry_username = registry_username
        self.registry_password = registry_password

        self.minimum_health_capacity = minimum_health_capacity

        self.acs_client = acsclient.ACSClient(self.acs_info)
        self.marathon_helper = marathon.Marathon(self.acs_client)

        self.portmappings_helper = portmappings.PortMappings()

    def __enter__(self):
        """
        Used when entering the 'with'
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when exiting the 'with' block
        """
        if self.acs_client:
            self.acs_client.shutdown()

    def _ensure_docker_compose(self, docker_compose_file):
        """
        1. Raises an error if there is no docker_compose_file present.
        2. Raises an error if the version specified in the docker_compose_file is not
        docker_compose_version.
        """
        docker_compose_expected_version = '2'
        if not os.path.isfile(docker_compose_file):
            raise Exception('Docker compose file "{}" was not found.'.format(docker_compose_file))
        with open(docker_compose_file, 'r') as f:
            compose_data = yaml.load(f)
            if 'version' not in compose_data.keys():
                raise Exception(
                    'Docker compose file "{}" is missing version information.'.format(
                        docker_compose_file))
            if not docker_compose_expected_version in compose_data['version']:
                raise Exception(
                    'Docker compose file "{}" has incorrect version. \
                    Only version "{}" is supported.'.format(
                        docker_compose_file,
                        docker_compose_expected_version))

    def _get_group_id(self, include_version=True):
        """
        Gets the group id.
        <group_name>.<first 8 chars of SHA-1 hash of group qualifier>.<group_version>
        """
        hash_qualifier = hashlib.sha1(self.group_qualifier)
        qualifier_digest = hash_qualifier.hexdigest()

        if include_version:
            return '/{}.{}.{}'.format(self.group_name, qualifier_digest[:8], self.group_version)

        return '/{}.{}.'.format(self.group_name, qualifier_digest[:8])

    def _parse_compose(self):
        """
        Parses the docker-compose file and returns the initial marathon.json file
        """
        group_name = self._get_group_id()
        all_apps = {'id': group_name, 'apps': []}
        docker_registry = dockerregistry.DockerRegistry(
            self.registry_host, self.registry_username, self.registry_password,
            self.marathon_helper)

        for service_name, service_info in self.compose_data['services'].items():
            # Get the app_json for the service
            service_parser = serviceparser.Parser(group_name, service_name, service_info)
            app_json = service_parser.get_app_json()

            # Add the registry auth URL if needed
            registry_auth_url = docker_registry.get_registry_auth_url()
            if registry_auth_url:
                app_json['uris'] = [registry_auth_url]
            all_apps['apps'].append(app_json)

        return all_apps

    def _predeployment_check(self):
        """
        Checks if services can be deployed and
        returns True if services are being updated or
        False if this is the first deployment
        """
        group_id = self._get_group_id(include_version=False)
        group_version_id = self._get_group_id()
        group_ids = self.marathon_helper.get_group_ids(group_id)
        group_count = len(group_ids)
        is_update = False
        existing_group_id = None

        if group_count > 1:
            raise Exception('Another deployment is already in progress')

        if group_count == 1:
            # Do an additional check that includes the group version
            groups_with_version = self.marathon_helper.get_group_ids(group_version_id)

            # Check if there's an existing group with the same version_id
            if len(groups_with_version) > 0:
                if group_version_id == groups_with_version[0]:
                    raise Exception('App with the same version already deployed')
            else:
                existing_group_id = group_ids[0]
                is_update = True

        return is_update, existing_group_id

    def _find_app_by_name(self, app_name, deployment_json):
        """
        Finds the app object in Marathon json
        """
        existing_app = None
        if not deployment_json or not 'apps' in deployment_json:
            return existing_app

        for app in sorted(deployment_json['apps']):
            # Gets the app name from the full id
            existing_app_name = app['id'].split('/')[-1]
            if existing_app_name.lower() == app_name.lower():
                existing_app = app
                break
        return existing_app

    def _create_or_update_vip_tuples(self, deployment_json, new_group_id, vip_tuples):
        """
        Extracts the VIPs from deployment json. If VIP label is already set, it will add it to a
        dictionary with the key set to new_group_id + app_name, so it's ready to be used with
        the new deployment. If VIP label is not set, it checks the portMappings key and
        creates a new VIP based on the servicePort.
        """
        if not deployment_json or not 'apps' in deployment_json:
            return vip_tuples

        new_group_id = new_group_id.rstrip('/')
        for app in deployment_json['apps']:
            app_id = app['id']

            # We already processed this app
            if app_id in vip_tuples:
                continue

            # Get the app name only, ignoring the group and everything else
            app_name = app_id.rstrip('/').split('/')[-1]
            new_id = '{}/{}'.format(new_group_id, app_name)

            if not 'labels' in app:
                continue

            # If app does not have a VIP set, we create a new one
            if not 'VIP' in app['labels']:
                try:
                    port_mappings = app['container']['docker']['portMappings']
                except KeyError:
                    raise Exception('Could not find container/docker/portMappings key')

                # Go through port mappings and create VIPs
                for port_mapping in port_mappings:
                    port = int(port_mapping['servicePort'])
                    x, y = divmod(port - 10000, 1<<8)
                    # We can use app_id here because the service is from the new
                    # deployment JSON
                    vip_tuples[str(new_id)] = (x, y)
                logging.info('Creating new VIP "%s" for "%s"', (x, y), new_id)
            else:
                # App already has a VIP, we need to use the new_group_id in the ID
                vip = app['labels']['VIP']
                if not '.' in vip:
                    continue

                vip_split = vip.split('.')
                vip_tuples[str(new_id)] = int(vip_split[0]), int(vip_split[1])
                logging.info('Reusing VIP "%s" for "%s"', vip, new_id)

        return vip_tuples

    def _get_next_color(self, deployment_json):
        """
        Gets the opposite color of first app in deployment json
        (all apps in a single deployment have the same color).
        If no color is set or color label is missing, we default to blue.
        """
        if not deployment_json or not 'apps' in deployment_json:
            raise ValueError('Empty deployment_json or missing "apps" key')

        if len(deployment_json['apps']) == 0:
            raise ValueError('No apps defined in deployment_json')

        first_app = deployment_json['apps'][0]

        if not 'labels' in first_app:
            return 'blue'

        if not 'color' in first_app['labels']:
            return 'blue'

        if first_app['labels']['color'].lower() == 'blue':
            return 'green'
        return 'blue'

    def _update_port_mappings(self, marathon_app, vip_tuples, service_info, current_color):
        """
        Updates portMappings in marathon_app for the service defined with service_info
        """
        marathon_app_id = marathon_app['id']
        vip = vip_tuples[marathon_app_id]
        port_mapping = self.portmappings_helper.get_port_mappings(vip, current_color, service_info)
        marathon_app['container']['docker']['portMappings'] = port_mapping
        marathon_app['labels']['VIP'] = str(vip[0]) + '.' + str(vip[1])
        marathon_app['labels']['color'] = current_color

    def _add_dependencies(self, marathon_app, vip_tuples, service_info):
        """
        Parses the 'depends_on' for service defined in service_info and
        uses vip_tuples to look-up dependency ids and updates the marathon_app.
        """
        if 'depends_on' in service_info:
            for dependency in service_info['depends_on']:
                all_dependency_ids = [t for t in vip_tuples if t.endswith(dependency)]
                if len(all_dependency_ids) > 0:
                    marathon_app['dependencies'].append(all_dependency_ids[0])

    def _add_host(self, marathon_app, app_id, vip_tuples, current_color, alias=None):
        """
        Adds a host entry ('add-host') to marathon_app in case it does not exist yet
        """
        created_vip = self.portmappings_helper.create_vip(current_color, vip_tuples[app_id])

        if alias:
            host_value = alias + ':' + created_vip
        else:
            host_value = app_id.split('/')[-1] + ':' + created_vip

        # If host does not exist yet, we add it
        if len([a for a in marathon_app['container']['docker']['parameters'] \
        if a['value'] == host_value]) == 0:
            marathon_app['container']['docker']['parameters'].append(
                {'key': 'add-host', 'value': host_value})

    def _add_hosts(self, marathon_app, vip_tuples, current_color):
        """
        Creates 'add-host' entries for the marathon_app by adding
        VIPs of all other services to 'add-host'
        """
        for app_id in vip_tuples:
            marathon_app_id = marathon_app['id']
            if not app_id.endswith(marathon_app_id.split('/')[-1]):
                self._add_host(marathon_app, app_id, vip_tuples, current_color)

    def deploy(self):
        """
        Deploys the services defined in docker-compose.yml file
        """
        is_update, existing_group_id = self._predeployment_check()

        # marathon_json is the instance we are working with and deploying
        marathon_json = self._parse_compose()

        # 1. Deploy the initial marathon_json file (instances = 0, no VIPs)
        self.marathon_helper.deploy_group(marathon_json)

        group_id = self._get_group_id()
        if not self.marathon_helper.is_group_id_unique(group_id):
            raise Exception('App with ID "{}" is not unique anymore'.format(group_id))

        new_deployment_json = self.marathon_helper.get_group(group_id)
        current_color = 'blue'
        vip_tuples = {}

        # 2. Figure out the VIPs and do a second deployment
        if is_update:
            existing_deployment_json = self.marathon_helper.get_group(existing_group_id)
            vip_tuples = self._create_or_update_vip_tuples(
                existing_deployment_json, group_id, vip_tuples)
            current_color = self._get_next_color(existing_deployment_json)

        # Create the VIPs from servicePorts for apps we dont have the VIPs for yet
        vip_tuples = self._create_or_update_vip_tuples(new_deployment_json, group_id, vip_tuples)

        # Go through the docker-compose file and update the corresponding marathon_app with
        # portMappings, VIP, color and links
        for service_name, service_info in self.compose_data['services'].items():
            # Get the corresponding marathon JSON for the service in docker-compose file
            marathon_app = [app for app in marathon_json['apps'] \
                                 if app['id'].endswith(service_name)][0]

            logging.info('Updating port mappings for "%s"', marathon_app['id'])
            self._update_port_mappings(marathon_app, vip_tuples, service_info, current_color)

            # Add hosts (VIPs) for all services, except the current one
            self._add_hosts(marathon_app, vip_tuples, current_color)

            # Update the dependencies and add 'add-host' entries for each link in the service
            if 'links' in service_info:
                for link_name in service_info['links']:
                    link_service_name = link_name
                    link_alias = link_name
                    if ':' in link_name:
                        # Split the link into service and alias
                        link_service_name = link_name.split(':')[0]
                        link_alias = link_name.split(':')[1]

                    # Get the VIP for the linked service
                    link_id = [t for t in vip_tuples if t.endswith(link_service_name)][0]
                    self._add_host(
                        marathon_app, link_id, vip_tuples, current_color, alias=link_alias)
                    logging.info('Adding dependency "%s" to "%s"', link_id, service_name)
                    marathon_app['dependencies'].append(link_id)

            # Handles the 'depends_on' key in docker-compose and adds any
            # dependencies to the dependncies list
            self._add_dependencies(marathon_app, vip_tuples, service_info)

        # Update the group with VIPs
        self.marathon_helper.update_group(marathon_json)

        # 3. Update the instances and do the final deployment
        if is_update:
            existing_deployment_json = self.marathon_helper.get_group(existing_group_id)

            # Get the number of instances for deployed services
            target_service_instances = {}
            for app in existing_deployment_json['apps']:
                full_app_id = app['id']
                # Just get the service name (e.g. service-a)
                app_id = full_app_id.split('/')[-1]
                new_apps = [a for a in new_deployment_json['apps'] \
                                    if a['id'].split('/')[-1] == app_id]
                new_app = new_apps[0]

                # Store the new app ID and the instances of existing app
                # so we can easily look it up when scaling
                target_service_instances[new_app['id']] = app['instances']

            for app in new_deployment_json['apps']:
                app_id = app['id']
                # Calculate the new instances for each service
                marathon_app = [app for app in marathon_json['apps'] \
                                 if app['id'] == app_id][0]
                instance_count = math.ceil(
                    (target_service_instances[app_id] * self.minimum_health_capacity) / 100)
                logging.info('Setting instances for app "%s" to %s',
                             marathon_app['id'], instance_count)
                marathon_app['instances'] = instance_count

            scale_factor = float(self.minimum_health_capacity)/100
            logging.info('Scale deployment "%s" by factor %s', existing_group_id, scale_factor)
            self.marathon_helper.scale_group(existing_group_id, scale_factor)

            logging.info('Update deployment "%s" with new instance counts', marathon_json['id'])
            self.marathon_helper.update_group(marathon_json)

            # Scale the existing deployment instances to 0
            logging.info('Scale deployment "%s" by factor %s', existing_group_id, 0)
            self.marathon_helper.scale_group(existing_group_id, 0)

            # Scale up new deployment instances to target instance count
            for app in new_deployment_json['apps']:
                app_id = app['id']
                marathon_app = [app for app in marathon_json['apps'] \
                                 if app['id'] == app_id][0]
                logging.info('Setting instances for app "%s" to %s',
                             marathon_app['id'], target_service_instances[app_id])
                marathon_app['instances'] = target_service_instances[app_id]

            logging.info('Scale instances in deployment "%s" to 0', existing_group_id)
            self.marathon_helper.update_group(existing_deployment_json)

            logging.info('Scale instances in deployment "%s" to target count', marathon_json['id'])
            self.marathon_helper.update_group(marathon_json)

            logging.info('Delete deployment "%s"', existing_group_id)
            self.marathon_helper.delete_group(existing_group_id)
        else:
            for app in marathon_json['apps']:
                app['instances'] = 1
            self.marathon_helper.update_group(marathon_json)
