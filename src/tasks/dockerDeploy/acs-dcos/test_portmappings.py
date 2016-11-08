import portmappings
import unittest
import json

class PortMappingsTest(unittest.TestCase):
    def test_create_instance(self):
        p = portmappings.PortMappings()
        self.assertIsNotNone(p)
    
    def test_is_number_valid(self):
        p = portmappings.PortMappings()
        self.assertTrue(p._is_number(0))

    def test_is_number_empty(self):
        p = portmappings.PortMappings()
        self.assertFalse(p._is_number(''))

    def test_is_number_string(self):
        p = portmappings.PortMappings()
        self.assertFalse(p._is_number('somestring'))

    def test_is_port_range_valid(self):
        p = portmappings.PortMappings()
        self.assertTrue(p._is_port_range('3000-3005'))

    def test_is_port_range_single_port(self):
        p = portmappings.PortMappings()
        self.assertFalse(p._is_port_range('3000'))

    def test_is_port_range_invalid(self):
        p = portmappings.PortMappings()
        self.assertFalse(p._is_port_range('3000-3001-3030'))

    def test_is_port_range_empty(self):
        p = portmappings.PortMappings()
        self.assertFalse(p._is_port_range(''))

    def test_is_port_range_not_a_number(self):
        p = portmappings.PortMappings()
        self.assertFalse(p._is_port_range('blah'))

    def test_is_port_range_missing_second_part(self):
        p = portmappings.PortMappings()
        self.assertFalse(p._is_port_range('3000-'))

    def test_split_port_range_valid(self):
        p = portmappings.PortMappings()
        self.assertEqual(p._split_port_range('3000-3005'), (3000, 3005))

    def test_split_port_range_single_port(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._split_port_range, '3000')

    def test_split_port_range_empty(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._split_port_range, '')

    def test_split_port_range_with_colon(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._split_port_range, '3000-3005:4000-4005')

    def test_are_port_ranges_same_length_valid(self):
        p = portmappings.PortMappings()
        self.assertTrue(p._are_port_ranges_same_length('3000-3005', '4000-4005'))

    def test_are_port_ranges_same_length_different_range(self):
        p = portmappings.PortMappings()
        self.assertFalse(p._are_port_ranges_same_length('3000-3005', '4000-4015'))

    def test_are_port_ranges_same_length_invalid(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._are_port_ranges_same_length, '3000', '4000-4015')

    def test_parse_private_ports_valid(self):
        p = portmappings.PortMappings()
        self.assertEquals(p._parse_private_ports({'expose': ['3000']}), [(3000, 3000)])

    def test_parse_private_ports_empty_service_data(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._parse_private_ports, {})

    def test_parse_private_ports_pair(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._parse_private_ports, {'expose': ['3000:3001']})
     
    def test_parse_private_ports_not_a_number(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._parse_private_ports, {'expose': ['blah']})

    def test_parse_internal_ports_pair(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080:80"]}
        self.assertEquals(p._parse_internal_ports(service_data), [(8080, 80)])

    def test_parse_internal_ports_single(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["5000"]}
        self.assertEquals(p._parse_internal_ports(service_data), [(5000, 5000)])

    def test_parse_internal_ports_two_single(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["5000", "3000"]}
        self.assertEquals(p._parse_internal_ports(service_data), [(5000, 5000), (3000, 3000)])

    def test_parse_internal_ports_pair_and_single(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080:1234", "3000"]}
        self.assertEquals(p._parse_internal_ports(service_data), [(8080, 1234), (3000, 3000)])

    def test_parse_internal_ports_two_pairs(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080:1234", "3030:3000"]}
        self.assertEquals(p._parse_internal_ports(service_data), [(8080, 1234), (3030, 3000)])

    def test_parse_internal_ports_single_range(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8085"]}
        self.assertEquals(p._parse_internal_ports(service_data), [(8080, 8080), (8081, 8081), (8082, 8082), (8083, 8083), (8084, 8084), (8085, 8085)])

    def test_parse_internal_ports_two_ranges(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8082:9090-9092"]}
        self.assertEquals(p._parse_internal_ports(service_data), [(8080, 9090), (8081, 9091), (8082, 9092)])

    def test_parse_internal_ports_two_ranges_single_and_pair(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8082:9090-9092", "5000", "1234:5432"]}
        self.assertEquals(p._parse_internal_ports(service_data), [(8080, 9090), (8081, 9091), (8082, 9092), (5000, 5000), (1234, 5432)])

    def test_parse_internal_ports_empty(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8082:9090-9092", "5000", "1234:5432", ""]}
        self.assertRaises(ValueError, p._parse_internal_ports, service_data)

    def test_parse_internal_ports_range_and_single_invalid(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8082:9090"]}
        self.assertRaises(ValueError, p._parse_internal_ports, service_data)

    def test_parse_internal_ports_empty_service_data(self):
        p = portmappings.PortMappings()
        service_data = {}
        self.assertRaises(ValueError, p._parse_internal_ports, service_data)

    def test_get_port_mappings_single_published_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_1': 'myvipname.internal:5000', 'VIP_0': '1.1.1.1:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'hostPort': 0}]
        service_data = {'ports': ["5000"]}
        self.assertEquals(p.get_port_mappings('1.1.1.1', service_data, 'myvipname'), expected)

    def test_get_port_mappings_single_exposed_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '1.1.1.1:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'hostPort': 0}]
        service_data = {'expose': ["5000"]}
        self.assertEquals(p.get_port_mappings('1.1.1.1', service_data, 'myvipname'), expected)

    def test_get_port_mappings_single_published_and_exposed_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_1': 'myvipname.internal:5000', 'VIP_0': '1.1.1.1:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'hostPort': 0}, {'labels': {'VIP_0': '1.1.1.1:3000'}, 'protocol': 'tcp', 'containerPort': 3000, 'hostPort': 0}]
        service_data = {'ports': ["5000"], 'expose': ["3000"]}
        self.assertEquals(sorted(p.get_port_mappings('1.1.1.1', service_data, 'myvipname')), sorted(expected))

    def test_get_port_mappings_single_port_range(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_1': 'myvipname.internal:5000', 'VIP_0': '1.1.1.1:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:5001', 'VIP_0': '1.1.1.1:5001'}, 'protocol': 'tcp', 'containerPort': 5001, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:5002', 'VIP_0': '1.1.1.1:5002'}, 'protocol': 'tcp', 'containerPort': 5002, 'hostPort': 0}]
        service_data = {'ports': ["5000-5002"]}
        self.assertEquals(p.get_port_mappings('1.1.1.1', service_data, 'myvipname'), expected)

    def test_get_port_mappings_port_range_and_single_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_1': 'myvipname.internal:5000', 'VIP_0': '1.1.1.1:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:5001', 'VIP_0': '1.1.1.1:5001'}, 'protocol': 'tcp', 'containerPort': 5001, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:5002', 'VIP_0': '1.1.1.1:5002'}, 'protocol': 'tcp', 'containerPort': 5002, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:3000', 'VIP_0': '1.1.1.1:3000'}, 'protocol': 'tcp', 'containerPort': 3000, 'hostPort': 0}]
        service_data = {'ports': ["5000-5002", "3000"]}
        self.assertEquals(p.get_port_mappings('1.1.1.1', service_data, 'myvipname'), expected)

    def test_get_port_mappings_port_range_pair(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_1': 'myvipname.internal:5000', 'VIP_0': '1.1.1.1:6000'}, 'protocol': 'tcp', 'containerPort': 6000, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:5001', 'VIP_0': '1.1.1.1:6001'}, 'protocol': 'tcp', 'containerPort': 6001, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:5002', 'VIP_0': '1.1.1.1:6002'}, 'protocol': 'tcp', 'containerPort': 6002, 'hostPort': 0}]
        service_data = {'ports': ["5000-5002:6000-6002"]}
        self.assertEquals(p.get_port_mappings('1.1.1.1', service_data, 'myvipname'), expected)

    def test_get_port_mappings_port_range_pair_and_expose(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_1': 'myvipname.internal:5000', 'VIP_0': '1.1.1.1:6000'}, 'protocol': 'tcp', 'containerPort': 6000, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:5001', 'VIP_0': '1.1.1.1:6001'}, 'protocol': 'tcp', 'containerPort': 6001, 'hostPort': 0}, {'labels': {'VIP_1': 'myvipname.internal:5002', 'VIP_0': '1.1.1.1:6002'}, 'protocol': 'tcp', 'containerPort': 6002, 'hostPort': 0}, {'labels': {'VIP_0': '1.1.1.1:4000'}, 'protocol': 'tcp', 'containerPort': 4000, 'hostPort': 0}]
        service_data = {'ports': ["5000-5002:6000-6002"], 'expose': ["4000"]}
        self.assertEquals(sorted(p.get_port_mappings('1.1.1.1', service_data, 'myvipname')), sorted(expected))

    def test_get_port_mappings_external_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_1': 'myvipname.internal:5000', 'VIP_0': '1.1.1.1:5000', 'VIP_2': 'www.example.com.external:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'hostPort': 0}]
        service_data = {'ports': ["5000"], 'labels': {'com.microsoft.acs.dcos.marathon.vhost': 'www.example.com:5000'} }
        self.assertEquals(p.get_port_mappings('1.1.1.1', service_data, 'myvipname'), expected)

    def test_get_port_mappings_external_no_internal_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '1.1.1.1:5000', 'VIP_2': 'www.example.com.external:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'hostPort': 0}]
        service_data = {'labels': {'com.microsoft.acs.dcos.marathon.vhost': 'www.example.com:5000'} }
        self.assertEquals(p.get_port_mappings('1.1.1.1', service_data, 'myvipname'), expected)

    def test_get_port_mappings_multiple_externals(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '1.1.1.1:8080', 'VIP_2': u'www.contoso.com.external:8080'}, 'protocol': 'tcp', 'containerPort': 8080, 'hostPort': 0}, {'labels': {'VIP_0': '1.1.1.1:8081', 'VIP_2': u'api.contoso.com.external:8081'}, 'protocol': 'tcp', 'containerPort': 8081, 'hostPort': 0}]
        service_data = {'labels': {'com.microsoft.acs.dcos.marathon.vhosts': '["www.contoso.com:8080", "api.contoso.com:8081"]' } }
        actual = p.get_port_mappings('1.1.1.1', service_data, 'myvipname')
        self.assertEquals(actual, expected)

    def test_get_port_mappings_string(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '1.1.1.1:5000', 'VIP_2': 'www.example.com.external:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'hostPort': 0}]
        service_data = {'labels': {'com.microsoft.acs.dcos.marathon.vhost=www.example.com:5000'} }
        self.assertEquals(p.get_port_mappings('1.1.1.1', service_data, 'myvipname'), expected)

    def test_get_port_mappings_string_list(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '1.1.1.1:8080', 'VIP_2': u'www.contoso.com.external:8080'}, 'protocol': 'tcp', 'containerPort': 8080, 'hostPort': 0}, {'labels': {'VIP_0': '1.1.1.1:8081', 'VIP_2': u'api.contoso.com.external:8081'}, 'protocol': 'tcp', 'containerPort': 8081, 'hostPort': 0}]
        service_data = {'labels': { "com.microsoft.acs.dcos.marathon.vhosts=[\"www.contoso.com:8080\", \"api.contoso.com:8081\"]" }}
        actual = p.get_port_mappings('1.1.1.1', service_data, 'myvipname')
        self.assertEquals(actual, expected)

    def test_parse_vhost_label(self):
        p = portmappings.PortMappings()
        label = '1.1.1.1:123'
        expected = ('1.1.1.1', 123)
        actual = p._parse_vhost_label(label)
        self.assertEquals(actual, expected)

    def test_parse_vhost_label_no_port(self):
        p = portmappings.PortMappings()
        label = '1.1.1.1'
        expected = ('1.1.1.1', 80)
        actual = p._parse_vhost_label(label)
        self.assertEquals(actual, expected)

    def test_parse_vhost_label_none(self):
        p = portmappings.PortMappings()
        actual = p._parse_vhost_label(None)
        self.assertIsNone(actual)

    def test_parse_vhosts_json_none(self):
        p = portmappings.PortMappings()
        actual = p._parse_vhost_json(None)
        self.assertIsNone(actual)

    def test_parse_vhosts_json(self):
        p = portmappings.PortMappings()
        label = '["example:123", "api.example:80"]'
        actual = p._parse_vhost_json(label)
        expected = { 'example': 123, 'api.example': 80}
        self.assertEquals(actual, expected)

    def test_parse_vhosts_json_invalid(self):
        p = portmappings.PortMappings()
        label = '//ewr"example:123", "api.example:80"]'
        self.assertRaises(ValueError, p._parse_vhost_json, label)

    def test_get_all_vhosts_no_labels(self):
        p = portmappings.PortMappings()
        service_data = {}
        expected = {}
        actual = p._get_all_vhosts(service_data)
        self.assertEquals(actual, expected)

    def test_get_all_vhosts_single_string(self):
        p = portmappings.PortMappings()
        service_data = { 'labels': {
            'com.microsoft.acs.dcos.marathon.vhost=example.com:80'
        }}
        expected = {'example.com': 80}
        actual = p._get_all_vhosts(service_data)
        self.assertEquals(actual, expected)

    def test_get_all_vhosts_single_dict(self):
        p = portmappings.PortMappings()
        service_data = { 'labels': {
            'com.microsoft.acs.dcos.marathon.vhost': 'example.com:80'
        }}
        expected = {'example.com': 80}
        actual = p._get_all_vhosts(service_data)
        self.assertEquals(actual, expected)

    def test_get_all_vhosts_single_json(self):
        p = portmappings.PortMappings()
        service_data = { 'labels': {
            'com.microsoft.acs.dcos.marathon.vhost=example.com:80'
        }}
        expected = {'example.com': 80}
        actual = p._get_all_vhosts(service_data)
        self.assertEquals(actual, expected)