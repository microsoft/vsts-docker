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
from exhibitor import Exhibitor
from nginx import LoadBalancerApp


class DockerComposeParser(object):
    def __init__(self, compose_file, master_url, acs_host, acs_port, acs_username,
                 acs_password, acs_private_key, group_name, group_qualifier, group_version,
                 registry_host, registry_username, registry_password,
                 minimum_health_capacity, check_dcos_version=False):

        self.cleanup_needed = False
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
        if check_dcos_version:
            self.acs_client.ensure_dcos_version()
        self.marathon_helper = marathon.Marathon(self.acs_client)
        self.exhibitor_helper = Exhibitor(self.marathon_helper)
        self.nginx_helper = LoadBalancerApp(self.marathon_helper)

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
        if not exc_type is SystemExit:
            self._cleanup()
        else:
            self._shutdown()

    def _shutdown(self):
        """
        Shuts down the acs client if needed
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
            raise Exception(
                'Docker compose file "{}" was not found.'.format(docker_compose_file))
        with open(docker_compose_file, 'r') as f:
            compose_data = yaml.load(f)
            if 'services' not in compose_data.keys():
                raise ValueError(
                    'Docker compose file "{}" is missing services information.'.format(
                        docker_compose_file))
            if 'version' not in compose_data.keys():
                raise ValueError(
                    'Docker compose file "{}" is missing version information.'.format(
                        docker_compose_file))
            if not docker_compose_expected_version in compose_data['version']:
                raise ValueError(
                    'Docker compose file "{}" has incorrect version. \
                    Only version "{}" is supported.'.format(
                        docker_compose_file,
                        docker_compose_expected_version))

    def _get_hash(self, str):
        """
        Gets the hashed string
        """
        hash_value = hashlib.sha1(str)
        digest = hash_value.hexdigest()
        return digest

    def _get_group_id(self, include_version=True):
        """
        Gets the group id.
        <group_name>.<first 8 chars of SHA-1 hash of group qualifier>.<group_version>
        """
        hash_qualifier = self._get_hash(self.group_qualifier)[:8]

        if include_version:
            return '/{}.{}.{}'.format(self.group_name, hash_qualifier, self.group_version)

        return '/{}.{}.'.format(self.group_name, hash_qualifier)

    def _get_vip_name(self, service_name):
        """
        Gets the vip name that includes hashed group name, qualifier,
        version and service name
        """
        qualifier_hash = self._get_hash(self.group_qualifier)
        return '{}.{}'.format(self._get_hash(self.group_name + qualifier_hash)[:8],
                              service_name)

    def _parse_compose(self):
        """
        Parses the docker-compose file and returns the initial marathon.json file
        """
        group_name = self._get_group_id()
        all_apps = {'id': group_name, 'apps': []}

        self.nginx_helper.ensure_exists(self.compose_data)
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
            raise Exception(
                'Another deployment is already in progress')

        if group_count == 1:
            # Do an additional check that includes the group version
            groups_with_version = self.marathon_helper.get_group_ids(group_version_id)

            # Check if there's an existing group with the same version_id
            if len(groups_with_version) > 0:
                if group_version_id == groups_with_version[0]:
                    raise Exception(
                        'App with the same version already deployed')
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

    def _create_or_update_private_ips(self, deployment_json, new_group_id):
        """
        Goes through the deployment json and uses 'servicePort' to
        create a new private IP.
        """
        private_ips = {}
        if not deployment_json or not 'apps' in deployment_json:
            return private_ips

        new_group_id = new_group_id.rstrip('/')
        for app in deployment_json['apps']:
            app_id = app['id']

            # Get the app name only, ignoring the group and everything else
            app_name = app_id.rstrip('/').split('/')[-1]
            new_id = '{}/{}'.format(new_group_id, app_name)

            try:
                port_mappings = app['container']['docker']['portMappings']
            except KeyError:
                pass

            if port_mappings is None:
                continue

            if not len(port_mappings):
                continue

            # Always get the first portMapping and use it to create the private IP
            port_mapping = port_mappings[0]
            port = int(port_mapping['servicePort'])
            x, y = divmod(port - 10000, 1<<8)
            ip = '10.64.' + str(x) + '.' + str(y)
            private_ips[str(new_id)] = ip
            logging.info('Creating new private IP "%s" for service "%s"', ip, new_id)

        return private_ips

    def _update_port_mappings(self, marathon_app, private_ips, service_info, vip_name):
        """
        Updates portMappings in marathon_app for the service defined with service_info
        """
        marathon_app_id = marathon_app['id']

        if not marathon_app_id in private_ips:
            return

        ip_address = private_ips[marathon_app_id]
        port_mapping = self.portmappings_helper.get_port_mappings(
            ip_address,
            service_info,
            vip_name)
        marathon_app['container']['docker']['portMappings'] = port_mapping

    def _add_dependencies(self, marathon_app, private_ips, service_info):
        """
        Parses the 'depends_on' for service defined in service_info and
        uses vip_tuples to look-up dependency ids and updates the marathon_app.
        """
        if 'depends_on' in service_info:
            for dependency in service_info['depends_on']:
                all_dependency_ids = [t for t in private_ips if t.endswith(dependency)]
                if len(all_dependency_ids) > 0:
                    # Check if the dependency is already added, before
                    # adding it, so we don't get dupes
                    exists = [d for d in marathon_app['dependencies'] if d.lower() == all_dependency_ids[0]]
                    if len(exists) == 0:
                        marathon_app['dependencies'].append(all_dependency_ids[0])

    def _add_host(self, marathon_app, app_id, private_ips, alias=None):
        """
        Adds a host entry ('add-host') to marathon_app in case it does not exist yet
        """
        created_vip = private_ips[app_id]
        if ':' in created_vip:
            split = created_vip.split(':')
            created_vip = split[0]

        if alias:
            host_value = alias + ':' + created_vip
        else:
            host_value = app_id.split('/')[-1] + ':' + created_vip

        # If host does not exist yet, we add it
        if len([a for a in marathon_app['container']['docker']['parameters'] \
        if a['value'] == host_value]) == 0:
            marathon_app['container']['docker']['parameters'].append(
                {'key': 'add-host', 'value': host_value})

    def _add_hosts(self, all_apps, marathon_app, private_ips):
        """
        Creates 'add-host' entries for the marathon_app by adding
        VIPs of all other services to 'add-host'
        """
        marathon_app_id = marathon_app['id']
        for app_id in private_ips:
            if not app_id.endswith(marathon_app_id.split('/')[-1]):
                if self._has_private_ip(all_apps, app_id):
                    self._add_host(marathon_app, app_id, private_ips)

    def _has_private_ip(self, all_apps, app_id):
        """
        Checks if app_id in all_apps contains at least
        one port mapping with VIP_0 set
        """
        apps = [app for app in all_apps \
                if app['id'].lower() == app_id.lower()]
        if len(apps) <= 0:
            return False
        app = apps[0]

        try:
            port_mappings = app['container']['docker']['portMappings']
        except KeyError:
            return False

        if port_mappings is None:
            return False

        for port_mapping in port_mappings:
            if not 'labels' in port_mapping:
                continue
            if 'VIP_0' in port_mapping['labels']:
                return True
        return False

    def _cleanup(self):
        """
        Removes the group we were trying to deploy in case exception occurs
        """
        if not self.cleanup_needed:
            self._shutdown()
            return

        try:
            group_id = self._get_group_id()
            logging.info('Removing "%s".', group_id)
            self.marathon_helper.delete_group(group_id)
        except Exception as remove_exception:
            raise remove_exception
        finally:
            self._shutdown()

    def deploy(self):
        """
        Deploys the services defined in docker-compose.yml file
        """
        is_update, existing_group_id = self._predeployment_check()

        # marathon_json is the instance we are working with and deploying
        marathon_json = self._parse_compose()

        # 1. Deploy the initial marathon_json file (instances = 0, no VIPs)
        self.marathon_helper.deploy_group(marathon_json)

        # At this point we need to clean up if anything
        # goes wrong
        self.cleanup_needed = True

        group_id = self._get_group_id()
        if not self.marathon_helper.is_group_id_unique(group_id):
            raise Exception(
                'App with ID "{}" is not unique anymore'.format(group_id))

        new_deployment_json = self.marathon_helper.get_group(group_id)

        # Create the VIPs from servicePorts for apps we dont have the VIPs for yet
        private_ips = self._create_or_update_private_ips(new_deployment_json, group_id)

        # Go through the docker-compose file and update the corresponding marathon_app with
        # portMappings, VIP, color and links
        for service_name, service_info in self.compose_data['services'].items():
            # Get the corresponding marathon JSON for the service in docker-compose file
            marathon_app = [app for app in marathon_json['apps'] \
                                 if app['id'].endswith('/' + service_name)][0]

            logging.info('Updating port mappings for "%s"', marathon_app['id'])
            self._update_port_mappings(
                marathon_app,
                private_ips,
                service_info,
                self._get_vip_name(service_name))

            # Handles the 'depends_on' key in docker-compose and adds any
            # dependencies to the dependencies list
            self._add_dependencies(marathon_app, private_ips, service_info)

        for service_name, service_info in self.compose_data['services'].items():
            # Get the corresponding marathon JSON for the service in docker-compose file
            marathon_app = [app for app in marathon_json['apps'] \
                                 if app['id'].endswith('/' + service_name)][0]

            # Add hosts (VIPs) for all services, except the current one
            self._add_hosts(marathon_json['apps'], marathon_app, private_ips)

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
                    link_id = [t for t in private_ips if t.endswith(link_service_name)][0]
                    # Make sure app with name link_id has a VIP_0

                    if not self._has_private_ip(marathon_json['apps'], link_id):
                        raise Exception(
                            "Can't link '{}' to '{}'. '{}' doesn't expose any ports"
                            .format(service_name, link_service_name, link_service_name))

                    self._add_host(marathon_app, link_id, private_ips, alias=link_alias)
                    logging.info('Adding dependency "%s" to "%s"', link_id, service_name)
                    marathon_app['dependencies'].append(link_id)

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

            logging.info('Scale instances in deployment "%s" to target count', marathon_json['id'])
            self.marathon_helper.update_group(marathon_json)

            logging.info('Delete deployment "%s"', existing_group_id)
            self.marathon_helper.delete_group(existing_group_id)
        else:
            for app in marathon_json['apps']:
                app['instances'] = 1
            self.marathon_helper.update_group(marathon_json)
