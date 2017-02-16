import unittest
from serviceparser import Parser
import yaml
import copy
import json
from groupinfo import GroupInfo
from registryinfo import RegistryInfo


class ServiceParserTests(unittest.TestCase):

    def _get_default_parser(self, service_info=None):
        group_info = GroupInfo('group_name', 'group_qualifier', 1)
        registry_info = RegistryInfo('host', 'username', 'password')

        if not service_info:
            service_info = {
                'image': 'some_image',
                'environment': {
                    'variable_one': 'value_one'
                },
                'expose': ['80'],
                'ports': ['8080']
            }
        service_name = 'my_service'
        service_parser = Parser(group_info, registry_info,
                                service_name, service_info)
        return service_parser

    def test_not_none(self):
        service_parser = self._get_default_parser()
        self.assertIsNotNone(service_parser)

    def test_get_service_name_label(self):
        service_name = 'my_service'
        service_parser = self._get_default_parser()
        expected = {'com.microsoft.acs.k8s.service_name': service_name}
        actual = service_parser._get_service_name_label()
        self.assertEquals(actual, expected)

    def test_get_empty_service_json(self):
        service_parser = self._get_default_parser()
        expected = {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": 'my_service'
            },
            "spec": {
                "selector": {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                },
                "ports": []
            }
        }
        actual = service_parser._get_empty_service_json()
        self.assertEquals(actual, expected)

    def test_get_empty_deployment_json(self):
        service_parser = self._get_default_parser()
        service_name = 'my_service'
        expected = {
            "apiVersion": "extensions/v1beta1",
            "kind": "Deployment",
            "metadata": {
                "name": service_name
            },
            "spec": {
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": {
                            'com.microsoft.acs.k8s.service_name': service_name
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": service_name
                        }],
                        "imagePullSecrets": []
                    }
                }
            }
        }
        actual = service_parser._get_empty_deployment_json()
        self.assertEquals(actual, expected)

    def test_add_label(self):
        service_parser = self._get_default_parser()
        service_parser._add_label('label_name', 'some_value')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'label_name': 'some_value',
                            'com.microsoft.acs.k8s.service_name': 'my_service'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_add_label_no_name(self):
        service_parser = self._get_default_parser()
        expected = copy.deepcopy(service_parser.deployment_json)
        service_parser._add_label('', 'some_value')
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_add_label_no_value(self):
        service_parser = self._get_default_parser()
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'some_label': '',
                            'com.microsoft.acs.k8s.service_name': 'my_service'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        service_parser._add_label('some_label', '')
        actual = service_parser.deployment_json

        self.assertEquals(actual, expected)

    def test_add_container_image(self):
        service_parser = self._get_default_parser()
        service_parser._add_container_image('my_service', 'some_image')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service',
                            'image': 'some_image'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_add_container_image_no_service(self):
        service_parser = self._get_default_parser()
        expected = copy.deepcopy(service_parser.deployment_json)
        service_parser._add_container_image('', 'some_image')
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_add_container_image_no_image(self):
        service_parser = self._get_default_parser()
        expected = copy.deepcopy(service_parser.deployment_json)
        service_parser._add_container_image('my_service', '')
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_parse_image(self):
        service_parser = self._get_default_parser()
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service',
                            'image': 'some_image'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }

        service_parser._parse_image('image')
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_parse_image_no_key(self):
        service_parser = self._get_default_parser()
        expected = copy.deepcopy(service_parser.deployment_json)
        service_parser._parse_image('blah')
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_add_image_pull_secret(self):
        service_parser = self._get_default_parser()
        service_parser._add_image_pull_secret('secret_name')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [{
                            'name': 'secret_name'
                        }],
                        'containers': [{
                            'name': 'my_service'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_add_image_pull_secret_no_name(self):
        service_parser = self._get_default_parser()
        expected = copy.deepcopy(service_parser.deployment_json)
        service_parser._add_image_pull_secret('')
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_add_container_port(self):
        service_parser = self._get_default_parser()
        service_parser._add_container_port(1234)
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service',
                            'ports': [{
                                'containerPort': 1234
                            }]
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_add_container_port_no_port(self):
        service_parser = self._get_default_parser()
        expected = copy.deepcopy(service_parser.deployment_json)
        service_parser._add_container_port(None)
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_get_service_json_no_service(self):
        service_parser = self._get_default_parser()
        self.assertIsNone(service_parser.get_service_json())

    def test_get_service_json(self):
        service_parser = self._get_default_parser()
        service_parser.service_added = True
        expected = {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": 'my_service'
            },
            "spec": {
                "selector": {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                },
                "ports": []
            }
        }
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_create_new_ingress_rule_default_path(self):
        service_parser = self._get_default_parser()
        expected = {
            "host": 'myhost.com',
            "http": {
                "paths": [{
                    "path": "/",
                    "backend": {
                        "serviceName": "my_service",
                        "servicePort": 1234
                    }
                }]
            }
        }
        actual = service_parser._create_new_ingress_rule(
            'myhost.com', 1234, 'my_service')
        self.assertEquals(actual, expected)

    def test_create_new_ingress_rule_empty_path(self):
        service_parser = self._get_default_parser()
        expected = {
            "host": 'myhost.com',
            "http": {
                "paths": [{
                    "path": "/",
                    "backend": {
                        "serviceName": "my_service",
                        "servicePort": 1234
                    }
                }]
            }
        }
        actual = service_parser._create_new_ingress_rule(
            'myhost.com', 1234, 'my_service', path=None)
        self.assertEquals(actual, expected)

    def test_create_new_ingress_rule_custom_path(self):
        service_parser = self._get_default_parser()
        expected = {
            "host": 'myhost.com',
            "http": {
                "paths": [{
                    "path": "/path",
                    "backend": {
                        "serviceName": "my_service",
                        "servicePort": 1234
                    }
                }]
            }
        }
        actual = service_parser._create_new_ingress_rule(
            'myhost.com', 1234, 'my_service', path="/path")
        self.assertEquals(actual, expected)

    def test_create_new_ingress_rule_no_host(self):
        service_parser = self._get_default_parser()
        self.assertRaises(
            ValueError, service_parser._create_new_ingress_rule, None, 1234, 'my_service')

    def test_create_new_ingress_rule_no_service(self):
        service_parser = self._get_default_parser()
        self.assertRaises(
            ValueError, service_parser._create_new_ingress_rule, 'myhost.com', 1234, '')

    def test_create_new_ingress_rule_no_port(self):
        service_parser = self._get_default_parser()
        self.assertRaises(
            ValueError, service_parser._create_new_ingress_rule, 'myhost.com', None, 'blah')

    def test_add_ingress_rule(self):
        service_parser = self._get_default_parser()
        expected = [{
            'host': 'host.com',
            'http': {
                'paths': [{
                    'path': '/',
                    'backend': {
                        'serviceName': 'my_service',
                        'servicePort': 1234
                    }
                }]
            }
        }]

        service_parser._add_ingress_rule('host.com', 1234, 'my_service')
        actual = service_parser.ingress_rules
        self.assertEquals(actual, expected)

    def test_add_ingress_rule_update_existing(self):
        service_parser = self._get_default_parser()
        service_parser.ingress_rules = [{
            'host': 'host.com',
            'http': {
                'paths': [{
                    'path': '/',
                    'backend': {
                        'serviceName': 'my_service',
                        'servicePort': 1234
                    }
                }]
            }
        }]

        expected = [{
            'host': 'host.com',
            'http': {
                'paths': [{
                    'path': '/',
                    'backend': {
                        'serviceName': 'my_service',
                        'servicePort': 1234
                    }
                }, {
                    'path': '/',
                    'backend': {
                        'serviceName': 'anotherservice',
                        'servicePort': 80
                    }
                }]
            }
        }]

        service_parser._add_ingress_rule('host.com', 80, 'anotherservice')
        actual = service_parser.ingress_rules
        self.assertEquals(actual, expected)

    def test_get_ingress_json(self):
        service_parser = self._get_default_parser()
        ingress_rules = [{
            "host": "host.com",
            "http": {
                "paths": [{
                    "path": "/",
                    "backend": {
                        "serviceName": "my_service",
                        "servicePort": 1234
                    }
                }]
            }
        }]

        service_parser.ingress_rules = ingress_rules
        expected = {"kind": "Ingress", "spec": {"rules": [{"host": "host.com", "http": {"paths": [{"path": "/", "backend": {
            "serviceName": "my_service", "servicePort": 1234}}]}}]}, "apiVersion": "extensions/v1beta1", "metadata": {"name": "my_service"}}

        actual = service_parser.get_ingress_json()
        self.assertEquals(actual, json.dumps(expected))

    def test_get_ingress_json_no_rules(self):
        service_parser = self._get_default_parser()
        self.assertIsNone(service_parser.get_ingress_json())

    def test_get_port_name(self):
        service_parser = self._get_default_parser()
        expected = "port-80"
        actual = service_parser._get_port_name(80)
        self.assertEquals(actual, expected)

    def test_get_port_name_multiple(self):
        service_parser = self._get_default_parser()
        service_parser.service_json['spec']['ports'].append({
            "name": "port-80",
            "protocol": "TCP",
            "targetPort": 8080,
            "port": 80
        })
        expected = "port-80-1"
        actual = service_parser._get_port_name(80)
        self.assertEquals(actual, expected)

    def test_create_service(self):
        service_parser = self._get_default_parser()
        self.assertFalse(service_parser.service_added)
        service_parser._create_service((80, 8080))
        expected = {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": 'my_service'
            },
            "spec": {
                "selector": {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                },
                "ports": [{
                    "name": "port-8080",
                    "protocol": "TCP",
                    "targetPort": 80,
                    "port": 8080
                }]
            }
        }
        self.assertTrue(service_parser.service_added)
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_create_service_existing_ports(self):
        service_parser = self._get_default_parser()
        self.assertFalse(service_parser.service_added)
        service_parser._create_service((80, 8080))
        expected = {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": 'my_service'
            },
            "spec": {
                "selector": {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                },
                "ports": [{
                    "name": "port-8080",
                    "protocol": "TCP",
                    "targetPort": 80,
                    "port": 8080
                }]
            }
        }
        service_parser._create_service((80, 8080))
        self.assertTrue(service_parser.service_added)
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_create_service_multiple_ports(self):
        service_parser = self._get_default_parser()
        self.assertFalse(service_parser.service_added)
        service_parser._create_service((80, 8080))
        expected = {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": 'my_service'
            },
            "spec": {
                "selector": {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                },
                "ports": [{
                    "name": "port-8080",
                    "protocol": "TCP",
                    "targetPort": 80,
                    "port": 8080
                }, {
                    "name": "port-8080-1",
                    "protocol": "TCP",
                    "targetPort": 81,
                    "port": 8080
                }]
            }
        }
        service_parser._create_service((81, 8080))
        self.assertTrue(service_parser.service_added)
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_port_exists_default(self):
        service_parser = self._get_default_parser()
        self.assertFalse(service_parser._port_exists((80, 8080)))

    def test_port_exists_none(self):
        service_parser = self._get_default_parser()
        self.assertFalse(service_parser._port_exists(None))

    def test_port_exists(self):
        service_parser = self._get_default_parser()
        service_parser.service_json['spec']['ports'].append({
            "name": 'port-8080',
            "protocol": "TCP",
            "targetPort": 80,
            "port": 8080
        })
        self.assertTrue(service_parser._port_exists((80, 8080)))

    def test_port_exists_false(self):
        service_parser = self._get_default_parser()
        service_parser.service_json['spec']['ports'].append({
            "name": 'port-8080',
            "protocol": "TCP",
            "targetPort": 80,
            "port": 8080
        })
        self.assertFalse(service_parser._port_exists((81, 8080)))

    def test_port_exists_multiple(self):
        service_parser = self._get_default_parser()
        service_parser.service_json['spec']['ports'].append({
            "name": 'port-8080',
            "protocol": "TCP",
            "targetPort": 80,
            "port": 8080
        })

        service_parser.service_json['spec']['ports'].append({
            "name": 'port-8080',
            "protocol": "TCP",
            "targetPort": 81,
            "port": 8080
        })
        self.assertTrue(service_parser._port_exists((81, 8080)))

    def test_parse_environment(self):
        service_parser = self._get_default_parser()
        service_parser._parse_environment('environment')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service',
                            'env': [{
                                'name': 'variable_one',
                                'value': 'value_one'
                            }]
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_parse_environment_list(self):
        service_info = {
            'image': 'some_image',
            'environment': ['variable_one=value_one', 'variable_two=value_two']
        }
        service_parser = self._get_default_parser(service_info)
        service_parser._parse_environment('environment')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service',
                            'env': [{
                                'name': 'variable_one',
                                'value': 'value_one'
                            }, {
                                'name': 'variable_two',
                                'value': 'value_two'
                            }]
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_parse_expose(self):
        service_parser = self._get_default_parser()

        expected = {
            'kind': 'Service',
            'spec': {
                'ports': [{
                    'targetPort': 80,
                    'protocol': 'TCP',
                    'name': 'port-80',
                    'port': 80
                }],
                'selector': {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                }
            },
            'apiVersion': 'v1',
            'metadata': {
                'name': 'my_service'
            }
        }

        service_parser._parse_expose('expose')
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_parse_expose_multiple_ports(self):
        service_info = {
            'image': 'some_image',
            'environment': {
                'variable_one': 'value_one'
            },
            'expose': ['80', '8080']
        }
        service_parser = self._get_default_parser(service_info)

        expected = {
            'kind': 'Service',
            'spec': {
                'ports': [{
                    'targetPort': 80,
                    'protocol': 'TCP',
                    'name': 'port-80',
                    'port': 80
                }, {
                    'targetPort': 8080,
                    'protocol': 'TCP',
                    'name': 'port-8080',
                    'port': 8080
                }],
                'selector': {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                }
            },
            'apiVersion': 'v1',
            'metadata': {
                'name': 'my_service'
            }
        }

        service_parser._parse_expose('expose')
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_parse_expose_no_expose(self):
        service_info = {
            'image': 'some_image',
            'environment': {
                'variable_one': 'value_one'
            }
        }
        service_parser = self._get_default_parser(service_info)

        expected = {
            'kind': 'Service',
            'spec': {
                'ports': [],
                'selector': {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                }
            },
            'apiVersion': 'v1',
            'metadata': {
                'name': 'my_service'
            }
        }

        service_parser._parse_expose('expose')
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_parse_ports(self):
        service_parser = self._get_default_parser()

        expected = {
            'kind': 'Service',
            'spec': {
                'ports': [{
                    'targetPort': 8080,
                    'protocol': 'TCP',
                    'name': 'port-8080',
                    'port': 8080
                }],
                'selector': {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                }
            },
            'apiVersion': 'v1',
            'metadata': {
                'name': 'my_service'
            }
        }

        service_parser._parse_ports('ports')
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_parse_ports_pair(self):
        service_info = {
            'image': 'some_image',
            'environment': {
                'variable_one': 'value_one'
            },
            'ports': ['80:8080']
        }
        service_parser = self._get_default_parser(service_info)
        expected = {
            'kind': 'Service',
            'spec': {
                'ports': [{
                    'targetPort': 80,
                    'protocol': 'TCP',
                    'name': 'port-8080',
                    'port': 8080
                }],
                'selector': {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                }
            },
            'apiVersion': 'v1',
            'metadata': {
                'name': 'my_service'
            }
        }

        service_parser._parse_ports('ports')
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_parse_ports_range(self):
        service_info = {
            'image': 'some_image',
            'environment': {
                'variable_one': 'value_one'
            },
            'ports': ['80-81:90-91']
        }
        service_parser = self._get_default_parser(service_info)
        expected = {
            'kind': 'Service',
            'spec': {
                'ports': [{
                    'targetPort': 80,
                    'protocol': 'TCP',
                    'name': 'port-90',
                    'port': 90
                }, {
                    'targetPort': 81,
                    'protocol': 'TCP',
                    'name': 'port-91',
                    'port': 91
                }],
                'selector': {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                }
            },
            'apiVersion': 'v1',
            'metadata': {
                'name': 'my_service'
            }
        }

        service_parser._parse_ports('ports')
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_parse_ports_and_expose_no_dupes(self):
        service_info = {
            'image': 'some_image',
            'environment': {
                'variable_one': 'value_one'
            },
            'ports': ['8080'],
            'expose': ['8080']
        }
        service_parser = self._get_default_parser(service_info)
        expected = {
            'kind': 'Service',
            'spec': {
                'ports': [{
                    'targetPort': 8080,
                    'protocol': 'TCP',
                    'name': 'port-8080',
                    'port': 8080
                }],
                'selector': {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                }
            },
            'apiVersion': 'v1',
            'metadata': {
                'name': 'my_service'
            }
        }

        service_parser._parse_ports('ports')
        service_parser._parse_expose('expose')
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_parse_ports_and_expose(self):
        service_info = {
            'image': 'some_image',
            'environment': {
                'variable_one': 'value_one'
            },
            'ports': ['80:8080'],
            'expose': ['8080']
        }
        service_parser = self._get_default_parser(service_info)
        expected = {
            'kind': 'Service',
            'spec': {
                'ports': [{
                    'targetPort': 80,
                    'protocol': 'TCP',
                    'name': 'port-8080',
                    'port': 8080
                }, {
                    'targetPort': 8080,
                    'protocol': 'TCP',
                    'name': 'port-8080-1',
                    'port': 8080
                }],
                'selector': {
                    'com.microsoft.acs.k8s.service_name': 'my_service'
                }
            },
            'apiVersion': 'v1',
            'metadata': {
                'name': 'my_service'
            }
        }
        service_parser._parse_ports('ports')
        service_parser._parse_expose('expose')
        actual = service_parser.service_json
        self.assertEquals(actual, expected)

    def test_parse_labels(self):
        service_info = {
            'labels': {'my_label': 'label_value'},
            'image': 'some_image',
        }
        service_parser = self._get_default_parser(service_info)
        service_parser._parse_labels('labels')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service',
                            'my_label': 'label_value'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_parse_labels_ignore_com_ms(self):
        service_info = {
            'labels': {
                'my_label': 'label_value',
                'com.microsoft.acs.kubernetes.vhosts': 'should_be_ignored'
            },
            'image': 'some_image',
        }
        service_parser = self._get_default_parser(service_info)
        service_parser._parse_labels('labels')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service',
                            'my_label': 'label_value'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_parse_labels_single_string(self):
        service_info = {
            'labels': {
                'my_label=some_value'
            },
            'image': 'some_image',
        }
        service_parser = self._get_default_parser(service_info)
        service_parser._parse_labels('labels')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service',
                            'my_label': 'some_value'
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_parse_labels_no_value(self):
        service_info = {
            'labels': {
                'my_label'
            },
            'image': 'some_image',
        }
        service_parser = self._get_default_parser(service_info)
        service_parser._parse_labels('labels')
        expected = {
            'kind': 'Deployment',
            'spec': {
                'template': {
                    'spec': {
                        'imagePullSecrets': [],
                        'containers': [{
                            'name': 'my_service'
                        }]
                    },
                    'metadata': {
                        'labels': {
                            'com.microsoft.acs.k8s.service_name': 'my_service',
                            'my_label': ''
                        }
                    }
                },
                'replicas': 1
            },
            'apiVersion': 'extensions/v1beta1',
            'metadata': {
                'name': 'my_service'
            }
        }
        actual = service_parser.deployment_json
        self.assertEquals(actual, expected)

    def test_get_deployment_json(self):
        service_info = {'environment': {'APPINSIGHTS_INSTRUMENTATIONKEY': None}, 'image': 'peterjausovec-exp.azurecr.io/peterjausovecsampleapp_service-a@sha256:67a44ab41d40e8c5b76530dd525008fef0d16f07b5e4e486ea569c88de543b9f',
                        'depends_on': ['service-b'], 'expose': ['8080'], 'labels': {'com.microsoft.acs.kubernetes.vhosts': '["www.containers.site", "api.containers.site:1234"]', 'some_label': 'label-value'}, 'ports': ['8080:80']}
        expected = {
            "kind": "Deployment",
            "spec": {
                "template": {
                    "spec": {
                        "imagePullSecrets": [{
                            "name": "host"
                        }],
                        "containers": [{
                            "image": "peterjausovec-exp.azurecr.io/peterjausovecsampleapp_service-a@sha256:67a44ab41d40e8c5b76530dd525008fef0d16f07b5e4e486ea569c88de543b9f",
                            "name": "my_service",
                            "env": [{
                                "name": "APPINSIGHTS_INSTRUMENTATIONKEY",
                                "value": ""
                            }],
                            "ports": [{
                                "containerPort": 80
                            }, {
                                "containerPort": 8080
                            }]
                        }]
                    },
                    "metadata": {
                        "labels": {
                            "some_label": "label-value",
                            "com.microsoft.acs.k8s.service_name": "my_service"
                        }
                    }
                },
                "replicas": 1
            },
            "apiVersion": "extensions/v1beta1",
            "metadata": {
                "name": "my_service"
            }
        }

        service_parser = self._get_default_parser(service_info)
        actual = service_parser.get_deployment_json()
        self.assertEquals(actual, json.dumps(expected))
