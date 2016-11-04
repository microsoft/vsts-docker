import portmappings
import unittest

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

    def test_parse_internal_ports_valid(self):
        p = portmappings.PortMappings()
        self.assertEquals(p._parse_internal_ports({'expose': ['3000']}), [(3000, 3000)]) 

    def test_parse_internal_ports_empty_service_data(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._parse_internal_ports, {}) 

    def test_parse_internal_ports_pair(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._parse_internal_ports, {'expose': ['3000:3001']})
     
    def test_parse_internal_ports_not_a_number(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._parse_internal_ports, {'expose': ['blah']})

    def test_parse_published_ports_pair(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080:80"]}
        self.assertEquals(p._parse_published_ports(service_data), [(8080, 80)])

    def test_parse_published_ports_single(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["5000"]}
        self.assertEquals(p._parse_published_ports(service_data), [(5000, 5000)])

    def test_parse_published_ports_two_single(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["5000", "3000"]}
        self.assertEquals(p._parse_published_ports(service_data), [(5000, 5000), (3000, 3000)])

    def test_parse_published_ports_pair_and_single(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080:1234", "3000"]}
        self.assertEquals(p._parse_published_ports(service_data), [(8080, 1234), (3000, 3000)])

    def test_parse_published_ports_two_pairs(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080:1234", "3030:3000"]}
        self.assertEquals(p._parse_published_ports(service_data), [(8080, 1234), (3030, 3000)])

    def test_parse_published_ports_single_range(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8085"]}
        self.assertEquals(p._parse_published_ports(service_data), [(8080, 8080), (8081, 8081), (8082, 8082), (8083, 8083), (8084, 8084), (8085, 8085)])

    def test_parse_published_ports_two_ranges(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8082:9090-9092"]}
        self.assertEquals(p._parse_published_ports(service_data), [(8080, 9090), (8081, 9091), (8082, 9092)])

    def test_parse_published_ports_two_ranges_single_and_pair(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8082:9090-9092", "5000", "1234:5432"]}
        self.assertEquals(p._parse_published_ports(service_data), [(8080, 9090), (8081, 9091), (8082, 9092), (5000, 5000), (1234, 5432)])

    def test_parse_published_ports_empty(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8082:9090-9092", "5000", "1234:5432", ""]}
        self.assertRaises(ValueError, p._parse_published_ports, service_data)

    def test_parse_published_ports_range_and_single_invalid(self):
        p = portmappings.PortMappings()
        service_data = {'ports': ["8080-8082:9090"]}
        self.assertRaises(ValueError, p._parse_published_ports, service_data)

    def test_parse_published_ports_empty_service_data(self):
        p = portmappings.PortMappings()
        service_data = {}
        self.assertRaises(ValueError, p._parse_published_ports, service_data)
    
    def test_create_port_mapping_valid(self):
        p = portmappings.PortMappings()
        expected = {'labels': {'VIP_0': '10.64.10.10:123'}, 'protocol': 'tcp', 'containerPort': 123, 'name': 'blue-123', 'hostPort': 0}
        self.assertEquals(p._create_port_mapping(123,321, 'blue', (10,10)), expected)

    def test_create_port_mapping_invalid_container_port(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._create_port_mapping, 'blah', 1, 'blue', (10,10))

    def test_create_port_mapping_invalid_vip_port(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._create_port_mapping, 1, 'blah', 'blue', (10,10))

    def test_create_port_mapping_missing_color(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p._create_port_mapping, 1, 1, '', (10,10))

    def test_create_port_mapping_invalid_tuple(self):
        p = portmappings.PortMappings()
        self.assertRaises(TypeError, p._create_port_mapping, 1, 1, 'blue', 'test')

    def test_create_vip_valid_blue(self):
        p = portmappings.PortMappings()
        self.assertEquals(p.create_vip('blue', (10,15)), '10.64.10.15')

    def test_create_vip_valid_green(self):
        p = portmappings.PortMappings()
        self.assertEquals(p.create_vip('green', (10,15)), '10.128.10.15')

    def test_create_vip_valid_cyan(self):
        p = portmappings.PortMappings()
        self.assertEquals(p.create_vip('cyan', (10,15)), '172.24.10.15')

    def test_create_vip_invalid_color(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p.create_vip, 'pink', (10,15))

    def test_create_vip_tuple_out_of_range_positive(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p.create_vip, 'green', (500,15))

    def test_create_vip_tuple_out_of_range_negative(self):
        p = portmappings.PortMappings()
        self.assertRaises(ValueError, p.create_vip, 'green', (100,-15))

    def test_get_port_mappings_blue_single_published_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '10.64.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'blue-5000', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'cyan-5000', 'hostPort': 0}]
        service_data = {'ports': ["5000"]}
        self.assertEquals(p.get_port_mappings((10,12), 'blue', service_data), expected)

    def test_get_port_mappings_green_single_exposed_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '10.128.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'green-5000', 'hostPort': 0}]
        service_data = {'expose': ["5000"]}
        self.assertEquals(p.get_port_mappings((10,12), 'green', service_data), expected)

    def test_get_port_mappings_blue_single_published_and_exposed_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '10.64.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'blue-5000', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'cyan-5000', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:3000'}, 'protocol': 'tcp', 'containerPort': 3000, 'name': 'blue-3000', 'hostPort': 0}]
        service_data = {'ports': ["5000"], 'expose': ["3000"]}
        self.assertEquals(p.get_port_mappings((10,12), 'blue', service_data), expected)

    def test_get_port_mappings_blue_single_port_range(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '10.64.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'blue-5000', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'cyan-5000', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:5001'}, 'protocol': 'tcp', 'containerPort': 5001, 'name': 'blue-5001', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5001'}, 'protocol': 'tcp', 'containerPort': 5001, 'name': 'cyan-5001', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:5002'}, 'protocol': 'tcp', 'containerPort': 5002, 'name': 'blue-5002', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5002'}, 'protocol': 'tcp', 'containerPort': 5002, 'name': 'cyan-5002', 'hostPort': 0}]
        service_data = {'ports': ["5000-5002"]}
        self.assertEquals(p.get_port_mappings((10,12), 'blue', service_data), expected)

    def test_get_port_mappings_blue_port_range_and_single_port(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '10.64.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'blue-5000', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 5000, 'name': 'cyan-5000', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:5001'}, 'protocol': 'tcp', 'containerPort': 5001, 'name': 'blue-5001', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5001'}, 'protocol': 'tcp', 'containerPort': 5001, 'name': 'cyan-5001', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:5002'}, 'protocol': 'tcp', 'containerPort': 5002, 'name': 'blue-5002', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5002'}, 'protocol': 'tcp', 'containerPort': 5002, 'name': 'cyan-5002', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:3000'}, 'protocol': 'tcp', 'containerPort': 3000, 'name': 'blue-3000', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:3000'}, 'protocol': 'tcp', 'containerPort': 3000, 'name': 'cyan-3000', 'hostPort': 0}]
        service_data = {'ports': ["5000-5002", "3000"]}
        self.assertEquals(p.get_port_mappings((10,12), 'blue', service_data), expected)

    def test_get_port_mappings_blue_port_range_pair(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '10.64.10.12:6000'}, 'protocol': 'tcp', 'containerPort': 6000, 'name': 'blue-6000', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 6000, 'name': 'cyan-5000', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:6001'}, 'protocol': 'tcp', 'containerPort': 6001, 'name': 'blue-6001', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5001'}, 'protocol': 'tcp', 'containerPort': 6001, 'name': 'cyan-5001', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:6002'}, 'protocol': 'tcp', 'containerPort': 6002, 'name': 'blue-6002', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5002'}, 'protocol': 'tcp', 'containerPort': 6002, 'name': 'cyan-5002', 'hostPort': 0}]
        service_data = {'ports': ["5000-5002:6000-6002"]}
        self.assertEquals(p.get_port_mappings((10,12), 'blue', service_data), expected)

    def test_get_port_mappings_blue_port_range_pair_and_expose(self):
        p = portmappings.PortMappings()
        expected = [{'labels': {'VIP_0': '10.64.10.12:6000'}, 'protocol': 'tcp', 'containerPort': 6000, 'name': 'blue-6000', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5000'}, 'protocol': 'tcp', 'containerPort': 6000, 'name': 'cyan-5000', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:6001'}, 'protocol': 'tcp', 'containerPort': 6001, 'name': 'blue-6001', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5001'}, 'protocol': 'tcp', 'containerPort': 6001, 'name': 'cyan-5001', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:6002'}, 'protocol': 'tcp', 'containerPort': 6002, 'name': 'blue-6002', 'hostPort': 0}, {'labels': {'VIP_0': '172.24.10.12:5002'}, 'protocol': 'tcp', 'containerPort': 6002, 'name': 'cyan-5002', 'hostPort': 0}, {'labels': {'VIP_0': '10.64.10.12:4000'}, 'protocol': 'tcp', 'containerPort': 4000, 'name': 'blue-4000', 'hostPort': 0}]
        service_data = {'ports': ["5000-5002:6000-6002"], 'expose': ["4000"]}
        self.assertEquals(p.get_port_mappings((10,12), 'blue', service_data), expected)
