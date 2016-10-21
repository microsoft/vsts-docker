#!/usr/bin/env python
import types

class PortMappings(object):
    def _is_number(self, str):
        """
        Checks if the string is a number or not
        """
        try:
            int(str)
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
            raise ValueError('Provided value is not a port range')
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

    def _parse_internal_ports(self, service_data):
        """
        Parses the 'expose' key in the docker-compose file and returns a list of tuples with port numbers. These tuples are used 
        to create portMappings (blue/green only) in the marathon.json file
        """
        port_tuple_list = []

        if not service_data:
            raise ValueError('No service data')

        if 'expose' not in service_data:
            return port_tuple_list

        for port_entry in service_data['expose']:
            if self._is_number(port_entry):
                port_tuple_list.append((int(port_entry), int(port_entry)))
            else:
                raise ValueError('Port is not a valid number')
        return port_tuple_list

    def _parse_published_ports(self, service_data):
        """
        Parses the 'ports' key in the docker-compose file and returns a list of tuples with port numbers. These tuples are used 
        to create portMappings (blue/green and cyan) in the marathon.json file
        """
        port_tuple_list = []

        if not service_data:
            raise ValueError('No service data')

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
                        # vp = vip_port, cp = container_port; we do +1 on the end range to include the last port as well
                        for vp, cp in zip(range(vip_start, vip_end + 1), range(container_start, container_end + 1)):
                            port_tuple_list.append((int(vp), int(cp)))
                    else:
                        raise ValueError('Port ranges are not equal in length')
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


    def _create_port_mapping(self, container_port, vip_port, color, service_mapping): 
        """ Creates a single port mapping with provided information
        """
        if not self._is_number(container_port):
            raise ValueError('Container port is not a valid number')
        
        if not self._is_number(vip_port):
            raise ValueError('VIP port is not a valid number')
        
        if not color:
            raise ValueError('Color is not set')
        
        if not isinstance(service_mapping, types.TupleType):
            raise TypeError('Service mapping has to be a tuple (e.g. (16,10)')

        return { 
            'containerPort': int(container_port),
            'hostPort': 0,
            'protocol': 'tcp',
            'name': color + '-' + str(vip_port),
            'labels': {
                'VIP_0': self.create_vip(color, service_mapping) + ':' + str(vip_port)
                }}

    def create_vip(self, color, tuple):
        """ 
        Takes a color and tuple that represents an IP address and creates a VIP
        """
        if tuple[0] > 255 or tuple[0] < 0 or tuple[1] > 255 or tuple[1] < 0:
            raise ValueError('Tuple value needs to be > 0 and < 255')
        if color == 'blue':
            return '10.64.' + str(tuple[0]) + '.' + str(tuple[1])
        elif color == 'green':
            return '10.128.' + str(tuple[0]) + '.' + str(tuple[1])
        elif color == 'cyan':
            return '172.24.' + str(tuple[0]) + '.' + str(tuple[1])
        else:
            raise ValueError('Color "{}" is not valid'.format(color))

    def get_port_mappings(self, service_tuple, color, service_data):
        """
        Creates portMappings entry for the marathon.json file. 
        """
        port_mappings = []
        
        # Need to add cyan portMapping for published ports ('ports' key in docker-compose)
        published_ports = self._parse_published_ports(service_data)

        for pp in published_ports:
            vip_port = pp[0]
            container_port = pp[1]
            port_mappings.append(self._create_port_mapping(container_port, vip_port, color, service_tuple))
            port_mappings.append(self._create_port_mapping(container_port, vip_port, 'cyan', service_tuple))

        # No need for cyan portMapping for internal ports ('expose' key in docker-compose)
        internal_ports = self._parse_internal_ports(service_data)
        for ip in internal_ports:
            vip_port = ip[0]
            container_port = ip[0]
            port_mappings.append(self._create_port_mapping(container_port, vip_port, color, service_tuple))
        return port_mappings
