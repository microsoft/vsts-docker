import os
import unittest

import mock

import dockercomposeparser


class DockerComposeParserTests(unittest.TestCase):
    test_root = os.path.dirname(os.path.realpath(__file__))
    test_compose_file = test_root + '/test_compose_1.yml'

    def test_create_parser(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        self.assertIsNotNone(p)

    def test_find_app_by_name_empty_json(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._find_app_by_name('app_name', {'apps':{}})
        self.assertIsNone(actual)

    def test_find_app_by_name_no_json(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._find_app_by_name('app_name', None)
        self.assertIsNone(actual)

    def test_find_app_by_name(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._find_app_by_name('app_name', {'apps':[{'id': 'my_group/app_name'}, {'id': 'my_group/second_app_name'}]})
        self.assertEquals('my_group/app_name', actual['id'])

    def test_find_app_by_name_not_found(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._find_app_by_name('missing_name', {'apps':[{'id': 'my_group/first_app_name'}, {'id': 'my_group/app_name'}]})
        self.assertIsNone(actual)

    def test_find_app_by_name_multiple(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._find_app_by_name('first_app_name', {'apps':[{'id': 'b_group/first_app_name'}, {'id': 'a_group/first_app_name'}]})
        self.assertEquals('a_group/first_app_name', actual['id'])

    def test_find_app_by_name_subfolders(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._find_app_by_name('app_name', {'apps':[{'id': 'my_group/version/app_name'}, {'id': 'my_group/anotherversion/second_app_name'}]})
        self.assertEquals('my_group/version/app_name', actual['id'])

    def test_find_app_by_name_no_slash(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._find_app_by_name('app_name', {'apps':[{'id': 'app_name'}, {'id': 'second_app_name'}]})
        self.assertEquals('app_name', actual['id'])


    def test_create_vip_tuples_empty_json(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        vip_tuples = {}
        actual = p._create_or_update_vip_tuples({'apps':{}}, 'new/group/id', vip_tuples)
        self.assertEquals({}, actual)

    def test_create_vip_tuples_none_json(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        vip_tuples = {}
        actual = p._create_or_update_vip_tuples(None, 'new/group/id', vip_tuples)
        self.assertEquals({}, actual)

    def test_create_vip_tuple(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'labels': {
                'VIP': '10.15'
            }
        }]}
        vip_tuples = {}
        expected = {'new/group/id/app_1': (10, 15)}
        actual = p._create_or_update_vip_tuples(apps_json, 'new/group/id', vip_tuples)
        self.assertEquals(expected, actual)

    def test_create_vip_tuple_extra_slash(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'labels': {
                'VIP': '10.15'
            }
        }]}
        vip_tuples = {}
        expected = {'new/group/id/app_1': (10, 15)}
        actual = p._create_or_update_vip_tuples(apps_json, 'new/group/id/', vip_tuples)
        self.assertEquals(expected, actual)

    def test_create_vip_tuple_multiple_apps(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'labels': {
                'VIP': '10.15'
            }
        }, {
            'id': 'group_2/app_2',
            'labels': {
                'VIP': '22.34'
            }
        }]}

        vip_tuples = {}
        expected = {'new/group/id/app_1': (10, 15), 'new/group/id/app_2': (22, 34)}
        actual = p._create_or_update_vip_tuples(apps_json, 'new/group/id/', vip_tuples)
        self.assertEquals(expected, actual)

    def test_create_vip_tuple_missing_vip(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'labels': {
                'VIP': '10.15'
            }
        }, {
            'id': 'group_2/app_2'
        }]}

        vip_tuples = {}
        expected = {'new/group/id/app_1': (10, 15)}
        actual = p._create_or_update_vip_tuples(apps_json, 'new/group/id/', vip_tuples)
        self.assertEquals(expected, actual)

    def test_create_vip_tuple_invalid_vip(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'labels': {
                'VIP': '10.15'
            }
        }, {
            'id': 'group_2/app_2',
            'labels': {
                'VIP': '123blah'
            }
        }]}

        vip_tuples = {}
        expected = {'new/group/id/app_1': (10, 15)}
        actual = p._create_or_update_vip_tuples(apps_json, 'new/group/id/', vip_tuples)
        self.assertEquals(expected, actual)

    def test_create_vip_tuple_create_new_vips(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'labels': {
            },
            'container': {
                'docker':{
                    'portMappings':[
                        {
                            'servicePort': 10001
                        }
                    ]
                }
            }
        }, {
            'id': 'group_2/app_2',
            'labels': {
            },
             'container': {
                'docker':{
                    'portMappings':[
                        {
                            'servicePort': 10002
                        }
                    ]
                }
            }
        }, {
            'id': 'group_3/app_3',
            'labels': {
                'VIP': '10.15'
            }
        }]}

        vip_tuples = {}
        actual = p._create_or_update_vip_tuples(apps_json, 'new/group/id/', vip_tuples)
        expected = {'new/group/id/app_1': (0, 1), 'new/group/id/app_3': (10, 15), 'new/group/id/app_2': (0, 2)}
        self.assertEquals(expected, actual)

    def test_get_next_color_missing(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        self.assertRaises(ValueError, p._get_next_color, {'apps': {}})

    def test_get_next_color_none(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        self.assertRaises(ValueError, p._get_next_color, None)

    def test_get_next_color(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._get_next_color({'apps':[{ 'labels': {'color': 'green'}}]})
        self.assertEquals('blue', actual)

    def test_get_next_color_1(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._get_next_color({'apps':[{ 'labels': {'color': 'blue'}}]})
        self.assertEquals('green', actual)

    def test_get_next_color_missing_color_label(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        actual = p._get_next_color({'apps':[{ 'labels': {}}]})
        self.assertEquals('blue', actual)

    def test_get_next_color_missing_labels(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        self.assertRaises(ValueError, p._get_next_color, {'apps':[]})

    def test_update_port_mappings(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        marathon_app = {
            'id': '/mygroup/service-b',
            'container': {
                'docker': {}
            },
            'labels': {}
        }
        vip_tuples = {'/mygroup/service-b': (0, 2), '/mygroup/service-a': (0, 3)}
        service_info = {'expose': [80]}
        current_color = 'blue'


        expected = { 
            'id': '/mygroup/service-b',
            'container': {
                'docker': {
                    'portMappings': [{
                        'labels': {'VIP_0': '10.64.0.2:80'},
                        'protocol': 'tcp',
                        'containerPort': 80,
                        'name': 'blue-80',
                        'hostPort': 0
                        }]
                    }
                },
            'labels': {
            'color': 'blue',
            'VIP': '0.2'
            }}

        p._update_port_mappings(marathon_app, vip_tuples, service_info, current_color)
        self.assertEquals(expected, marathon_app)

    def test_add_dependencies(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        marathon_app = {'dependencies': []}
        vip_tuples = {'/mygroup/service-b': (0, 2), '/mygroup/service-a': (0, 3)}
        service_info = {'depends_on': 'service-b'}
        expected = {'dependencies': ['/mygroup/service-b']}

        p._add_dependencies(marathon_app, vip_tuples, service_info)
        self.assertEquals(expected, marathon_app)

    def test_add_dependencies_no_depends_on(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        marathon_app = {}
        vip_tuples = {'/mygroup/service-b': (0, 2), '/mygroup/service-a': (0, 3)}
        service_info = {}

        p._add_dependencies(marathon_app, vip_tuples, service_info)
        self.assertEquals({}, marathon_app)

    def test_add_dependencies_no_tuple(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        marathon_app = {}
        vip_tuples = {'/mygroup/service-a': (0, 3)}
        service_info = {'depends_on': 'service-b'}

        p._add_dependencies(marathon_app, vip_tuples, service_info)
        self.assertEquals({}, marathon_app)

    def test_add_host(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        marathon_app = {'container': {
            'docker': {
                'parameters': []
            }
        }}
        vip_tuples = {'/mygroup/service-b': (0, 2), '/mygroup/service-a': (0, 3)}
        expected = {'container': {
            'docker': {
                'parameters': [{'value': 'service-a:10.64.0.3', 'key': 'add-host'}]
                }
            }
        }
        p._add_host(marathon_app, '/mygroup/service-a', vip_tuples, 'blue')
        self.assertEquals(expected, marathon_app)

    def test_add_host_alias(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        marathon_app = {'container': {
            'docker': {
                'parameters': []
            }
        }}
        vip_tuples = {'/mygroup/service-b': (0, 2), '/mygroup/service-a': (0, 3)}
        expected = {'container': {
            'docker': {
                'parameters': [{'value': 'myalias:10.64.0.3', 'key': 'add-host'}]
                }
            }
        }
        p._add_host(marathon_app, '/mygroup/service-a', vip_tuples, 'blue','myalias')
        self.assertEquals(expected, marathon_app)

    def test_add_hosts(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        marathon_app = {
            'id': '/mygroup/service-a',
            'container': {
                'docker': {
                    'parameters': []
                }
        }}
        expected = {'container': {'docker': {'parameters': [{'value': 'service-c:10.64.0.4', 'key': 'add-host'}, {'value': 'service-b:10.64.0.2', 'key': 'add-host'}]}}, 'id': '/mygroup/service-a'}
        vip_tuples = {'/mygroup/service-c': (0, 4), '/mygroup/service-b': (0, 2), '/mygroup/service-a': (0, 3)}
        p._add_hosts(marathon_app, vip_tuples, 'blue')
        self.assertEquals(expected, marathon_app)