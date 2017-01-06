import json
import logging
import pipes
import re

from portparser import PortParser


class Parser(object):

    def __init__(self, group_info, registry_info, service_name, service_info):
        self.service_name = service_name
        self.service_info = service_info
        self.registry_info = registry_info
        self.group_info = group_info
        self.deployment_json = self._get_empty_deployment_json()
        self.service_json = self._get_empty_service_json()
        self.ingress_rules = []
        self.service_added = False

        self.port_parser = PortParser(self.service_info)

    def _add_label(self, name, value):
        """
        Adds a label to deployment JSON
        """
        self.deployment_json['spec']['template'][
            'metadata']['labels'][name] = value

    def _add_container_image(self, name, image):
        """
        Adds a container with name and image to the JSON
        """
        for container in self.deployment_json['spec']['template']['spec']['containers']:
            if container['name'] == name:
                container['image'] = image
                break

    def _add_image_pull_secret(self, name):
        """
        Adds image pull secret to the deployment JSON
        """
        self.deployment_json['spec']['template']['spec']['imagePullSecrets'].append({
            "name": name})

    def _add_container_port(self, container_port):
        """
        Adds a container port
        """
        # TODO: Do we always grab the first container? Or do we need
        # to pass in the name of the container to find the right one
        if not 'ports' in self.deployment_json['spec']['template']['spec']['containers'][0]:
            self.deployment_json['spec']['template'][
                'spec']['containers'][0]['ports'] = []

        self.deployment_json['spec']['template']['spec']['containers'][0]['ports'].append({
            "containerPort": container_port})

    def get_service_json(self):
        """
        Gets the service JSON for service
        """
        if self.service_added:
            return json.dumps(self.service_json)
        return None

    def get_ingress_json(self):
        """
        Gets the ingress JSON for the service
        """
        # TODO: should we have 1 ingress resource per docker-compose or one
        # per service?
        if self.ingress_rules:
            return json.dumps({
                "apiVersion": "extensions/v1beta1",
                "kind": "Ingress",
                "metadata": {
                    "name": "{}-ingress".format(self.group_info.get_namespace())
                },
                "labels":{
                    "group_name": self.group_info.name,
                    "group_qualifier": self.group_info.qualifier,
                    "group_id": self.group_info.get_id()
                },
                "spec": {
                    "rules": self.ingress_rules
                }
            })
        return None

    # TODO: This should return an object with everything that needs to be deployed
    # e.g. deployment.json, service.json, ???
    def get_deployment_json(self):
        """
        Gets the deployment JSON for the service in docker-compose
        """
        self._add_label('group_name', self.group_info.name)
        self._add_label('group_qualifier', self.group_info.qualifier)
        self._add_label('group_version', self.group_info.version)
        self._add_label('group_id', self.group_info.get_id())
        self._add_label('service_name', self.service_name)

        self._add_image_pull_secret(self.registry_info.host)

        # self.['id'] = '{}/{}'.format(self.group_name, self.service_name)

        for key in self.service_info:
            # We look for the method named _parse_{key} (for example: _parse_ports)
            # and execute it to parse that key.
            # If we decide to support more stuff from docker-compose, we
            # can simply add a method named _parse_NEWKEY and implement how the
            # key translates to Marathon JSON.
            method_name = '_parse_{}'.format(key)
            if hasattr(self, method_name):
                logging.info('Parsing key "%s"', key)
                method_to_call = getattr(self, method_name)
                method_to_call(key)

        vhosts = self.port_parser.get_all_vhosts()
        for vhost in vhosts:
            host_name = vhost
            service_port = vhosts[vhost]
            self._add_ingress_rule(host_name, service_port, self.service_name)

        return json.dumps(self.deployment_json)

    def _create_new_ingress_rule(self, host_name, service_port, service_name):
        """
        Creates a new ingress rule and adds it to the list of rules.
        """
        self.ingress_rules.append({
            "host": host_name,
            "http": {
                "paths": [{
                    # TODO: How can we specify path in docker-compose
                    "path": "/",
                    "backend": {
                        "serviceName": service_name,
                        "servicePort": service_port
                    }
                }]
            }
        })

    def _add_ingress_rule(self, host_name, service_port, service_name):
        """
        Create a new ingress rule or updates an existing one
        """
        if not self.ingress_rules:
            self._create_new_ingress_rule(
                host_name, service_port, service_name)
        else:
            # Check if there's an existing rule for host_name
            existing_rules = [
                rule for rule in self.ingress_rules if rule["host"] == host_name]
            if len(existing_rules) == 0:
                self._create_new_ingress_rule(
                    host_name, service_port, service_name)
            else:
                # Add a new path to an existing rule
                existing_rule = existing_rules[0]
                existing_rule['http']['paths'].append({
                    "backend": {
                        "path": "/",
                        "serviceName": service_name,
                        "servicePort": service_port
                    }
                })

    def _parse_image(self, key):
        """
        Parses the 'image' key
        """
        if key in self.service_info:
            self._add_container_image(
                self.service_name, self.service_info[key])

    def _create_service(self, port_tuple):
        # TODO: Do we need to create multiple ports if we have 'expose' and
        # 'ports' key?
        self.service_added = True
        self.service_json['spec']['ports'].append({
            "name": "port-{}".format(port_tuple[1]),
            "protocol": "TCP",
            "targetPort": port_tuple[0],
            "port": port_tuple[1]
        })

    def _parse_environment(self, key):
        """
        Parses the 'environment' key
        """
        containers_key = self.deployment_json['spec'][
            'template']['spec']['containers'][0]
        if key in self.service_info:
            if 'env' not in containers_key:
                containers_key['env'] = []
            for env_pair in self.service_info[key]:
                if isinstance(self.service_info[key], list):
                    if '=' in env_pair:
                        env_split = env_pair.split('=')
                        env_var_name = env_split[0]
                        env_var_value = env_split[1]
                        containers_key['env'].append(
                            {"name": env_var_name, "value": env_var_value})
                    else:
                        # If environment var does not have a value set
                        containers_key['env'].append(
                            {"name": env_pair, "value": ''})
                else:
                    value = self.service_info[key][env_pair]
                    if value is None:
                        containers_key['env'].append(
                            {"name": env_pair, "value": ''})
                    else:
                        containers_key['env'].append(
                            {"name": env_pair, "value": str(value)})

    def _parse_expose(self, key):
        """
        Parses the 'expose' key
        """
        # TODO: How is 'expose' different from 'ports' ???
        if key in self.service_info:
            private_ports = self.port_parser.parse_private_ports()
            for port_tuple in private_ports:
                self._add_container_port(port_tuple[1])
                self._create_service(port_tuple)

    def _parse_ports(self, key):
        """
        Parses the 'ports' key
        """
        if key in self.service_info:
            internal_ports = self.port_parser.parse_internal_ports()
            for port_tuple in internal_ports:
                # TODO: What do we do with host port???
                # (hostPort:containerPort)
                # targetPort == containerPort
                self._add_container_port(port_tuple[1])
                self._create_service(port_tuple)

    def _parse_labels(self, key):
        """
        Parses the 'labels' key
        """
        if key in self.service_info:
            # TODO (peterj): Parse healthcheck labels here
            # # Add healthchecks (if any healthcheck labels are set)
            # healthcheck_helper = healthcheck.HealthCheck(self.service_info[key])
            # healthcheck_json = healthcheck_helper.get_health_check_config()
            # if not healthcheck_json is None:
            #     self.app_json['healthChecks'] = healthcheck_json

            for label in self.service_info[key]:
                if label.lower().startswith('com.microsoft.acs.kubernetes.vhost'):
                    continue

                if isinstance(self.service_info[key], dict):
                    self._add_label(label, str(self.service_info[key][label]))
                else:
                    if '=' in label:
                        label_split = label.split('=')
                        label_name = label_split[0]
                        label_value = label_split[1]
                        self._add_label(label_name, str(label_value))
                    else:
                        # label without a value
                        self._add_label(label, '')

    def _get_empty_deployment_json(self):
        deployment_json = {
            "apiVersion": "extensions/v1beta1",
            "kind": "Deployment",
            "metadata": {
                "name": self.service_name
            },
            "spec": {
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": {
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": self.service_name
                        }],
                        "imagePullSecrets": []
                    }
                }
            }
        }

        return deployment_json

    def _get_empty_service_json(self):
        """
        Gets the empty service JSON for service that's being parsed
        """
        return {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": self.service_name
            },
            "spec": {
                "selector": {
                    "group_id": self.group_info.get_id(),
                    "service_name": self.service_name
                },
                "ports": [],
            }
        }

    def _to_quoted_string(self, args):
        """
        Converts arguments to a properly quoted string
        """
        cmd_string = ''

        if not args:
            return args

        if isinstance(args, list):
            for arg in args:
                cmd_string += pipes.quote(str(arg)) + ' '
        else:
            cmd_string = pipes.quote(args)
        return cmd_string.strip()
