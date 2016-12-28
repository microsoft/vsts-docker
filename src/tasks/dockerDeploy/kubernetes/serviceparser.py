import logging
import pipes
import re
import json


class Parser(object):

    def __init__(self, group_info, registry_info, service_name, service_info):
        self.service_name = service_name
        self.service_info = service_info
        self.registry_info = registry_info
        self.group_info = group_info
        self.deployment_json = {}

    def _add_label(self, name, value):
        """
        Adds a label to deployment JSON
        """
        self.deployment_json['spec']['template'][
            'metadata']['labels'][name] = value

    def _add_container(self, name, image):
        """
        Adds a container with name and image to the JSON
        """
        self.deployment_json['spec']['template']['spec']['containers'].append({
            'name': name,
            'image': image
        })

    def _add_image_pull_secret(self, name):
        """
        Adds image pull secret to the deployment JSON
        """
        self.deployment_json['spec']['template']['spec']['imagePullSecrets'].append({
            'name': name})

    def _add_container_port(self, container_port):
        """
        Adds a container port
        """
        # TODO: Do we always grab the first container? Or do we need
        # to pass in the name of the container to find the right one

        if not 'ports' in self.deployment_json['spec']['template']['spec']['containers'][0]:
            self.deployment_json['spec']['template']['spec']['containers'][0]['ports'] = []

        self.deployment_json['spec']['template']['spec']['containers'][0]['ports'].append({
            'containerPort': container_port})

    def get_deployment_json(self):
        """
        Gets the app.json for the service in docker-compose
        """
        self.deployment_json = self._get_empty_deployment_json()
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
        return json.dumps(self.deployment_json)

    def _parse_image(self, key):
        """
        Parses the 'image' key
        """
        if key in self.service_info:
            self._add_container(self.service_name, self.service_info[key])

    def _parse_ports(self, key):
        """
        Parses the 'ports' key
        """
        if key in self.service_info:
            internal_ports = self._parse_internal_ports()
            for port_tuple in internal_ports:
                # TODO: What do we do with host port???
                self._add_container_port(port_tuple[1])

    def _parse_private_ports(self):
        """
        Parses the 'expose' key in the docker-compose file and returns a
        list of tuples with port numbers. These tuples are used
        to create portMappings (blue/green only) in the marathon.json file
        """
        port_tuple_list = []

        if 'expose' not in self.service_info:
            return port_tuple_list

        for port_entry in self.service_info['expose']:
            if self._is_number(port_entry):
                port_tuple_list.append((int(port_entry), int(port_entry)))
            else:
                raise ValueError(
                    'Port number "%s" is not a valid number', port_entry)
        return port_tuple_list

    def _parse_internal_ports(self):
        """
        Parses the 'ports' key in the docker-compose file and returns a list of
        tuples with port numbers. These tuples are used to create
        portMappings (blue/green and cyan) in the marathon.json file
        """
        port_tuple_list = []

        if 'ports' not in self.service_info:
            return port_tuple_list

        for port_entry in self.service_info['ports']:
            if ':' in str(port_entry):
                split = port_entry.split(':')
                vip_port = split[0]
                container_port = split[1]
                if self._is_port_range(vip_port) and self._is_port_range(container_port):
                    # "8080-8090:9080-9090"
                    if self._are_port_ranges_same_length(vip_port, container_port):
                        vip_start, vip_end = self._split_port_range(vip_port)
                        container_start, container_end = self._split_port_range(
                            container_port)
                        # vp = vip_port, cp = container_port; we do +1 on the end range to
                        # include the last port as well
                        for vp, cp in zip(range(vip_start, vip_end + 1), range(container_start, container_end + 1)):
                            port_tuple_list.append((int(vp), int(cp)))
                    else:
                        raise ValueError('Port ranges "{}" and "{}" are not equal in length',
                                         vip_port, container_port)
                else:
                    # "8080:8080"
                    if self._is_number(vip_port) and self._is_number(container_port):
                        port_tuple_list.append(
                            (int(vip_port), int(container_port)))
                    else:
                        # e.g. invalid entry: 8080-8082:9000
                        raise ValueError(
                            'One of the ports is not a valid number or a valid range')
            else:
                if self._is_port_range(port_entry):
                    # "3000-3005"
                    range_start, range_end = self._split_port_range(port_entry)
                    for i in range(range_start, range_end + 1):
                        port_tuple_list.append((i, i))
                else:
                    # "3000"
                    if self._is_number(port_entry):
                        port_tuple_list.append(
                            (int(port_entry), int(port_entry)))
                    else:
                        raise ValueError(
                            'One of the ports is not a valid number')
        return port_tuple_list

    def _is_number(self, input_str):
        """
        Checks if the string is a number or not
        """
        try:
            int(input_str)
            return True
        except ValueError:
            return False

    def _is_port_range(self, port_entry):
        """
        Checks if the provided string is a port entry or not
        """
        if not port_entry:
            return False

        if '-' in str(port_entry) and str(port_entry).count('-') == 1:
            split = port_entry.split('-')
            first_part = split[0]
            second_part = split[1]
            return self._is_number(first_part) and self._is_number(second_part)
        return False

    def _split_port_range(self, port_range):
        """
        Splits a port range and returns a tuple with start and end port
        """
        if not self._is_port_range(port_range):
            raise ValueError(
                'Provided value "%s" is not a port range', port_range)
        split = port_range.split('-')
        return (int(split[0]), int(split[1]))

    def _are_port_ranges_same_length(self, first_range, second_range):
        """
        Checks if two port ranges are the same length
        """

        if not self._is_port_range(first_range) or not self._is_port_range(second_range):
            raise ValueError(
                'At least one of the provided values is not a port range')

        first_split_start, first_split_end = self._split_port_range(
            first_range)
        second_split_start, second_split_end = self._split_port_range(
            second_range)

        return len(range(first_split_start, first_split_end)) == len(range(second_split_start, second_split_end))

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
                        "containers": [],
                        "imagePullSecrets": []
                    }
                }
            }
        }

        return deployment_json

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
