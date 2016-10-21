import hashlib
import math
import os

import acsinfo
import dockerregistry
import marathon
import portmappings
import yaml

class DockerComposeParser(object):
    def __init__(self, compose_file, master_url, acs_host, acs_port, acs_username,
                 acs_password, acs_private_key, group_name, group_qualifier, group_version,
                 registry_name, registry_username, registry_password,
                 minimum_health_capacity):

        if not os.path.isfile(compose_file):
            raise OSError('Error: File {} was not found'.format(compose_file))

        with open(compose_file, 'r') as compose_stream:
            self.compose_data = yaml.load(compose_stream)

        self.acs_info = acsinfo.AcsInfo(acs_host, acs_port, acs_username,
                                        acs_password, acs_private_key, master_url)

        self.group_name = group_name
        self.group_qualifier = group_qualifier
        self.group_version = group_version

        self.registry_name = registry_name
        self.registry_username = registry_username
        self.registry_password = registry_password

        self.minimum_health_capacity = minimum_health_capacity

        self.marathon_helper = marathon.Marathon(self.acs_info)

        self.portmappings_helper = portmappings.PortMappings()

    def _get_empty_marathon_json(self):
        marathon_json = {
            'id': '',
            'cpus': 0.1,
            'mem': 256,
            'instances': 0,
            'container': {
                'docker': {
                    'network': 'BRIDGE',
                    'portMappings': [{
                        'containerPort': 0,
                        'hostPort': 0,
                        'protocol': 'tcp',
                        'labels': {
                        }
                    }],
                    "parameters": []
                }
            },
            'labels': {
                'HAPROXY_GROUP': 'internal'
            },
            'dependencies': [],
            'env': {},
            'ports': []
        }
        return marathon_json

    def _get_group_id(self, include_version=True):
        """
        Gets the group id.
        <group_name>.<first 8 chars of SHA-1 has of group qualifier>.<group_version>
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
            self.registry_name, self.registry_username, self.registry_password, self.acs_info)

        for service_name, service_info in self.compose_data['services'].items():
            marathon_json = self._get_empty_marathon_json()
            marathon_json['id'] = group_name + '/' + service_name

            marathon_json['container']['docker']['image'] = service_info['image']
            registry_auth_url = docker_registry.get_registry_auth_url()
            marathon_json['uris'] = [registry_auth_url]

            if 'environment' in service_info:
                for env_pair in service_info['environment']:
                    if '=' in env_pair:
                        env_split = env_pair.split('=')
                        env_var_name = env_split[0]
                        env_var_value = env_split[1]
                        marathon_json['env'][env_var_name] = env_var_value

            if 'labels' in service_info:
                for label in service_info['labels']:
                    if isinstance(label, str):
                        if '=' in label:
                            label_split = label.split('=')
                            label_name = label_split[0]
                            label_value = label_split[1]
                            marathon_json['labels'][label_name] = label_value
                    elif isinstance(label, dict):
                        for label_name in label:
                            marathon_json['labels'][label_name] = label[label_name]

            if 'ports' in service_info:
                port_tuple_list = self.portmappings_helper._parse_published_ports(service_info)

                if len(port_tuple_list) > 0:
                    # PORT should be the same as PORT0
                    marathon_json['env']['PORT'] = str(port_tuple_list[0][1])
                    for i, p in enumerate(port_tuple_list):
                        container_port = p[1]
                        marathon_json['env'].update({'PORT' + str(i): str(container_port)})

            marathon_json['healthChecks'] = self._get_health_check_config()
            all_apps['apps'].append(marathon_json)

        return all_apps

    def _predeployment_check(self):
        """
        Checks if services can be deployment and
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

    def deploy(self):
        """
        Deploys the services defined in docker-compose.yml file
        """
        is_update, existing_group_id = self._predeployment_check()
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
            for app in new_deployment_json['apps']:
                # Get the service id only (without the group)
                full_app_id = app['id']
                app_id = full_app_id.split('/')[-1]

                existing_apps = [a for a in existing_deployment_json['apps'] \
                                    if a['id'].split('/')[-1] == app_id]

                # If we can't find the app, it means
                # this is a new service that was added
                # to the compose file
                if len(existing_apps) == 0:
                    continue
                elif len(existing_apps) > 1:
                    # There's more than 1 app found
                    raise Exception('Found multiple apps with id {}'.format(app_id))

                existing_app = existing_apps[0]
                if existing_app:
                    vip = existing_app['labels']['VIP']
                    vip_split = vip.split('.')
                    vip_tuples[str(full_app_id)] = int(vip_split[0]), int(vip_split[1])
                    if existing_app['labels']['color'] == 'blue':
                        current_color = 'green'

        port_mappings = []

        # Create the VIPs from servicePorts for
        # apps we dont have the VIPs for yet
        for app in new_deployment_json['apps']:
            app_id = app['id']

            # If we already have a VIP for this app we can continue.
            # This will happen if we are doing an update.
            if app_id in vip_tuples:
                continue

            try:
                port_mappings = app['container']['docker']['portMappings']
            except KeyError:
                raise Exception('Could not find container/docker/portMappings key')

            for port_mapping in port_mappings:
                if str(app_id) not in vip_tuples:
                    vip_tuples[str(app_id)] = []
                port = int(port_mapping['servicePort'])
                x, y = divmod(port - 10000, 1<<8)
                vip_tuples[str(app_id)] = (x, y)

        # Go through the docker-compose file and update the corresponding marathon_app with
        # portMappings, VIP, color and links
        for service_name, service_info in self.compose_data['services'].items():
            # Get the corresponding marathon JSON for the service in
            # docker-compose file
            marathon_app = [app for app in marathon_json['apps'] \
                                 if app['id'].endswith(service_name)][0]

            marathon_app_id = marathon_app['id']

            # portMappings
            vip = vip_tuples[marathon_app_id]
            port_mapping = self.portmappings_helper.get_port_mappings(vip, current_color, service_info)
            marathon_app['container']['docker']['portMappings'] = port_mapping
            marathon_app['labels']['VIP'] = str(vip[0]) + '.' + str(vip[1])
            marathon_app['labels']['color'] = current_color

            # Update the dependencies and add 'add-host' entries
            # for each link in the service
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
                    service_vip = vip_tuples[link_id]
                    created_vip = self.portmappings_helper.create_vip(current_color, service_vip)
                    marathon_app['container']['docker']['parameters'].append(
                        {'key': 'add-host', 'value': link_alias + ':' + created_vip})
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
                marathon_app['instances'] = math.ceil(
                    (target_service_instances[app_id] * self.minimum_health_capacity) / 100)

            scale_factor = float(self.minimum_health_capacity)/100
            print 'Scale deployment "{}" by factor {}'.format(existing_group_id, scale_factor)
            self.marathon_helper.scale_group(existing_group_id, scale_factor)

            print 'Update deployment "{}" with new instance counts'.format(marathon_json['id'])
            self.marathon_helper.update_group(marathon_json)

            # Scale the existing deployment instances to 0
            for app in existing_deployment_json['apps']:
                app['instances'] = 0
                del app['fetch']
            del existing_deployment_json['version']

            # Scale up new deployment instances to target instance count
            for app in new_deployment_json['apps']:
                app_id = app['id']
                marathon_app = [app for app in marathon_json['apps'] \
                                 if app['id'] == app_id][0]
                marathon_app['instances'] = target_service_instances[app_id]

            print 'Scale instances in deployment "{}" to 0'.format(existing_group_id)
            self.marathon_helper.update_group(existing_deployment_json)

            print 'Scale instances in deployment "{}" to target count'.format(marathon_json['id'])
            self.marathon_helper.update_group(marathon_json)

            print 'Delete deployment "{}"'.format(existing_group_id)
            self.marathon_helper.delete_group(existing_group_id)
        else:
            for app in marathon_json['apps']:
                app['instances'] = 1
            self.marathon_helper.update_group(marathon_json)

    def _get_health_check_config(self):
        return [{
            "portIndex": 0,
            "protocol": "TCP",
            "gracePeriodSeconds": 300,
            "intervalSeconds": 5,
            "timeoutSeconds": 20,
            "maxConsecutiveFailures": 3
        }]
