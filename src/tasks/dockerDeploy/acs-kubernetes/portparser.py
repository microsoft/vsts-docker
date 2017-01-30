import json

class PortParser(object):
    def __init__(self, service_info):
        self.service_info = service_info

    def parse_private_ports(self):
        """
        Parses the 'expose' key in the docker-compose file and returns a
        list of tuples with port numbers.
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

    def parse_internal_ports(self):
        """
        Parses the 'ports' key in the docker-compose file and returns a list of
        tuples with port numbers.
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


    def get_all_vhosts(self):
        """
        Gets a dictionary with all vhosts and their ports
        """
        vhost_label = 'com.microsoft.acs.kubernetes.vhost'
        vhosts_label = 'com.microsoft.acs.kubernetes.vhosts'
        all_vhosts = {}

        if 'labels' not in self.service_info:
            return {}

        for label in self.service_info['labels']:
            if label.lower() == vhosts_label:
                parsed = self._parse_vhost_json(self.service_info['labels'][label])
                all_vhosts = self._merge_dicts(all_vhosts, parsed)
            elif label.lower() == vhost_label:
                vhost_item = self.service_info['labels'][label]
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

    def _merge_dicts(self, dict_a, dict_b):
        """
        Merges two dictionaries
        """
        result = dict_a.copy()
        result.update(dict_b)
        return result