import json
import types


class PortMappings(object):
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
            raise ValueError('Provided value "%s" is not a port range', port_range)
        split = port_range.split('-')
        return (int(split[0]), int(split[1]))

    def _are_port_ranges_same_length(self, first_range, second_range):
        """
        Checks if two port ranges are the same length
        """

        if not self._is_port_range(first_range) or not self._is_port_range(second_range):
            raise ValueError('At least one of the provided values is not a port range')

        first_split_start, first_split_end = self._split_port_range(first_range)
        second_split_start, second_split_end = self._split_port_range(second_range)

        return len(range(first_split_start, first_split_end)) == len(range(second_split_start, second_split_end))

    def _parse_private_ports(self, service_data):
        """
        Parses the 'expose' key in the docker-compose file and returns a
        list of tuples with port numbers. These tuples are used
        to create portMappings (blue/green only) in the marathon.json file
        """
        port_tuple_list = []

        if not service_data:
            raise ValueError('service_data not provided')

        if 'expose' not in service_data:
            return port_tuple_list

        for port_entry in service_data['expose']:
            if self._is_number(port_entry):
                port_tuple_list.append((int(port_entry), int(port_entry)))
            else:
                raise ValueError('Port number "%s" is not a valid number', port_entry)
        return port_tuple_list

    def _parse_internal_ports(self, service_data):
        """
        Parses the 'ports' key in the docker-compose file and returns a list of
        tuples with port numbers. These tuples are used to create
        portMappings (blue/green and cyan) in the marathon.json file
        """
        port_tuple_list = []

        if not service_data:
            raise ValueError('service_data not provided')

        if 'ports' not in service_data:
            return port_tuple_list

        for port_entry in service_data['ports']:
            if ':' in str(port_entry):
                split = port_entry.split(':')
                vip_port = split[0]
                container_port = split[1]
                if self._is_port_range(vip_port) and self._is_port_range(container_port):
                    # "8080-8090:9080-9090"
                    if self._are_port_ranges_same_length(vip_port, container_port):
                        vip_start, vip_end = self._split_port_range(vip_port)
                        container_start, container_end = self._split_port_range(container_port)
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
                        port_tuple_list.append((int(vip_port), int(container_port)))
                    else:
                        # e.g. invalid entry: 8080-8082:9000
                        raise ValueError('One of the ports is not a valid number or a valid range')
            else:
                if self._is_port_range(port_entry):
                    # "3000-3005"
                    range_start, range_end = self._split_port_range(port_entry)
                    for i in range(range_start, range_end + 1):
                        port_tuple_list.append((i, i))
                else:
                    # "3000"
                    if self._is_number(port_entry):
                        port_tuple_list.append((int(port_entry), int(port_entry)))
                    else:
                        raise ValueError('One of the ports is not a valid number')
        return port_tuple_list

    def _get_port_mapping_json(self):
        return {
            'containerPort': 0,
            'hostPort': 0,
            'protocol': 'tcp',
            'labels': {
            }
        }

    def _parse_vhost_label(self, vhost_label):
        """
        Parses the vhost label string (host:[port]) and
        returns a tuple (host, port)
        """
        if not vhost_label:
            return None

        vhost = vhost_label
        vhost_port = 80
        if ':' in vhost_label:
            vhost_split = vhost_label.split(':')
            vhost = vhost_split[0]
            vhost_port = vhost_split[1]

        return vhost, int(vhost_port)

    def _parse_vhost_json(self, vhost_json):
        """
        Parse the vhosts JSON value
        """
        if not vhost_json:
            return None

        vhost_items = json.loads(vhost_json)
        parsed = {}
        for item in vhost_items:
            vhost, port = self._parse_vhost_label(item)
            parsed[vhost] = port
        return parsed

    def _merge_dicts(self, dict_a, dict_b):
        """
        Merges two dictionaries
        """
        result = dict_a.copy()
        result.update(dict_b)
        return result

    def _get_all_vhosts(self, service_data):
        """
        Gets a dictionary with all vhosts and their ports
        """
        vhost_label = 'com.microsoft.acs.dcos.marathon.vhost'
        vhosts_label = 'com.microsoft.acs.dcos.marathon.vhosts'
        all_vhosts = {}

        if not 'labels' in service_data:
            return {}

        for label in service_data['labels']:
            if label.lower() == vhosts_label:
                parsed = self._parse_vhost_json(service_data['labels'][label])
                all_vhosts = self._merge_dicts(all_vhosts, parsed)
            elif label.lower() == vhost_label:
                vhost_item = service_data['labels'][label]
                vhost, port = self._parse_vhost_label(vhost_item)
                all_vhosts[vhost] = port
            else:
                if '=' in label:
                    split = label.split('=')
                    if split[0].lower() == vhost_label:
                        # "vhost='www.contoto.com:80'"
                        vhost, port = self._parse_vhost_label(split[1])
                        all_vhosts[vhost] = port
                    elif split[0].lower() == vhosts_label:
                        # "vhosts=['www.blah.com:80','api.blah.com:81']"
                        parsed = self._parse_vhost_json(split[1].replace("'", '"'))
                        all_vhosts = self._merge_dicts(all_vhosts, parsed)
        return all_vhosts

    def _set_external_port_mappings(self, service_data, ip_address, existing_port_mappings):
        all_vhosts = self._get_all_vhosts(service_data)
        for vhost in all_vhosts:
            vhost_added = False
            port = all_vhosts[vhost]
            port = str(port).strip()
            external_vip = vhost + '.external' + ':' + port
            for port_mapping in existing_port_mappings:
                if str(port_mapping['containerPort']).strip() == str(port):
                    port_mapping['labels']['VIP_2'] = external_vip
                    vhost_added = True
            if not vhost_added:
                # Create a new port mapping
                port_mapping = self._get_port_mapping_json()
                port_mapping['containerPort'] = int(port)
                port_mapping['labels']['VIP_0'] = ip_address + ':' + port
                port_mapping['labels']['VIP_2'] = external_vip
                existing_port_mappings.append(port_mapping)

    def _get_internal_port_mappings(self, service_data, ip_address,
                                    vip_name, existing_port_mappings):
        """
        Gets the internal ports from the service data and updates the
        existing_port_mappings array
        """
        internal_ports = self._parse_internal_ports(service_data)

        for internal_port in internal_ports:
            port_mapping = self._get_port_mapping_json()
            vip_port = internal_port[0]
            container_port = internal_port[1]

            existing_mapping = False
            for existing_port_mapping in existing_port_mappings:
                if str(existing_port_mapping['containerPort']).strip() == str(container_port):
                    # No need to add VIP_0 as it already exists
                    existing_port_mapping['labels']['VIP_1'] = \
                        vip_name + '.internal' + ':' + str(vip_port)
                    existing_mapping = True
                    break
            # If we have a completely new mapping
            if not existing_mapping:
                port_mapping['containerPort'] = int(container_port)
                port_mapping['labels']['VIP_0'] = ip_address + ':' + str(container_port)
                port_mapping['labels']['VIP_1'] = vip_name + '.internal' + ':' + str(vip_port)
                existing_port_mappings.append(port_mapping)

    def _get_private_port_mappings(self, service_data, ip_address):
        """
        Creates a list of port mappings with private ports
        """
        port_mappings = []
        private_ports = self._parse_private_ports(service_data)

        for private_port in private_ports:
            port_mapping = self._get_port_mapping_json()
            container_port = private_port[0]
            port_mapping['containerPort'] = int(container_port)
            port_mapping['labels']['VIP_0'] = ip_address + ':' + str(container_port)
            port_mappings.append(port_mapping)

        return port_mappings

    def get_port_mappings(self, ip_address, service_data, vip_name):
        """
        Creates portMappings entry for the marathon.json file.
        """
        if ':' in ip_address:
            split = ip_address.split(':')
            ip_address = split[0]

        all_port_mappings = self._get_private_port_mappings(service_data, ip_address)
        self._get_internal_port_mappings(
            service_data, ip_address, vip_name, all_port_mappings)
        self._set_external_port_mappings(service_data, ip_address, all_port_mappings)
        return all_port_mappings
