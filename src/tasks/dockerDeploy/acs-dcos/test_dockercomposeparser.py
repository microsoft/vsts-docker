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

    def test_create_private_ips_empty_json(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        vip_tuples = {}
        actual = p._create_or_update_private_ips({'apps':{}}, 'new/group/id', vip_tuples)
        self.assertEquals({}, actual)

    def test_create_private_ips_none_json(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)
        vip_tuples = {}
        actual = p._create_or_update_private_ips(None, 'new/group/id', vip_tuples)
        self.assertEquals({}, actual)

    def test_create_ip(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'container': {
                'docker': {
                    'portMappings':[{
                        'labels': {},
                        'protocol': 'tcp',
                        'containerPort': 0,
                        'hostPort': 0,
                        'servicePort': 10000
                    }]
                }
            }
        }]}

        ips = {}
        expected = {'new/group/id/app_1': '10.64.0.0'}
        actual = p._create_or_update_private_ips(apps_json, 'new/group/id', ips)
        self.assertEquals(expected, actual)

    def test_create_private_ips_extra_slash(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'container': {
                'docker': {
                    'portMappings':[{
                        'labels': {},
                        'protocol': 'tcp',
                        'containerPort': 0,
                        'hostPort': 0,
                        'servicePort': 10000
                    }]
                }
            }
        }]}
        ips = {}
        expected = {'new/group/id/app_1': '10.64.0.0'}
        actual = p._create_or_update_private_ips(apps_json, 'new/group/id/', ips)
        self.assertEquals(expected, actual)

    def test_create_private_ips_multiple_apps(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'container': {
                'docker': {
                    'portMappings':[{
                        'labels': {},
                        'servicePort': 10000}]
                    }
                }
            },
            {
                'id': 'group_2/app_2',
                'container': {
                'docker': {
                    'portMappings':[{
                        'labels': {},
                        'servicePort': 10001
                    }]
                    }
                }
            }]
        }

        ips = {}
        expected = {'new/group/id/app_1': '10.64.0.0', 'new/group/id/app_2': '10.64.0.1'}
        actual = p._create_or_update_private_ips(apps_json, 'new/group/id/', ips)
        self.assertEquals(expected, actual)

    def test_create_private_ips_missing_vip(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'container': {
                'docker': {
                    'portMappings':[{
                        'labels': {},
                        'protocol': 'tcp',
                        'containerPort': 0,
                        'hostPort': 0,
                        'servicePort': 10000}]
                    }
                }
            },
            {
                'id': 'group_2/app_2'
            }]
        }

        vip_tuples = {}
        self.assertRaises(Exception, p._create_or_update_private_ips, apps_json, 'new/group/id/', vip_tuples)

    def test_create_private_ips_switch_ip(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'container': {
                'docker':{
                    'portMappings':[
                        {
                            'labels': {
                                'VIP_0': '10.64.0.0'
                            }
                        }
                    ]
                }
            }
        }]}

        ips = {}
        actual = p._create_or_update_private_ips(apps_json, 'new/group/id/', ips)
        expected = {'new/group/id/app_1': '10.128.0.0'}
        self.assertEquals(expected, actual)

    def test_create_private_ips_existing_ip(self):
        p = dockercomposeparser.DockerComposeParser(
            self.test_compose_file, 'masterurl', None, None, None, None, None,
            'groupname', 'groupqualifier', '1',
            'registryhost', 'registryuser', 'registrypassword', 100)

        apps_json = {'apps':[{
            'id': 'group_1/app_1',
            'container': {
                'docker':{
                    'portMappings':[
                        {
                            'labels': {
                                'VIP_0': '10.64.0.0'
                            }
                        }
                    ]
                }
            }
        }]}

        ips = { 'group_1/app_1': '10.64.0.0'}
        actual = p._create_or_update_private_ips(apps_json, 'new/group/id/', ips)
        expected = {'group_1/app_1': '10.64.0.0'}
        self.assertEquals(expected, actual)

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
        vip_tuples = {'/mygroup/service-b': '1.1.1.1', '/mygroup/service-a': '1.1.1.2'}
        expected = {'container': {
            'docker': {
                'parameters': [{'value': 'service-a:1.1.1.2', 'key': 'add-host'}]
                }
            }
        }
        p._add_host(marathon_app, '/mygroup/service-a', vip_tuples)
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
        vip_tuples = {'/mygroup/service-b': '1.1.1.1', '/mygroup/service-a': '1.1.1.2'}
        expected = {'container': {
            'docker': {
                'parameters': [{'value': 'myalias:1.1.1.2', 'key': 'add-host'}]
                }
            }
        }
        p._add_host(marathon_app, '/mygroup/service-a', vip_tuples,'myalias')
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
        expected = {'container': {'docker': {'parameters': [{'value': 'service-c:1.1.1.1', 'key': 'add-host'}, {'value': 'service-b:1.1.1.2', 'key': 'add-host'}]}}, 'id': '/mygroup/service-a'}
        vip_tuples = {'/mygroup/service-c': '1.1.1.1', '/mygroup/service-b': '1.1.1.2', '/mygroup/service-a': '1.1.1.3'}
        p._add_hosts(marathon_app, vip_tuples)
        self.assertEquals(expected, marathon_app)