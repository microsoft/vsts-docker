import json
import os
import unittest

import yaml

import serviceparser


class ServiceParserTests(unittest.TestCase):
    def test_not_none(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        self.assertIsNotNone(p)

    def test_to_quoted_string(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        actual = p._to_quoted_string('a b c d')
        self.assertEquals('\'a b c d\'', actual)

    def test_to_quoted_string_list(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        actual = p._to_quoted_string(['a', 'b', 'c d'])
        self.assertEquals('a b \'c d\'', actual)

    def test_to_quoted_string_none(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        actual = p._to_quoted_string(None)
        self.assertEquals(None, actual)

    def test_to_quoted_string_empty(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        actual = p._to_quoted_string('')
        self.assertEquals('', actual)

    def test_parse_command_string(self):
        expected = {'cmd': "'bundle exec thin -p 3000'"}
        p = serviceparser.Parser('groupname', 'myservice', {'command': 'bundle exec thin -p 3000'})
        p._parse_command('command')
        self.assertEquals(expected, p.app_json)

    def test_parse_command_list(self):
        expected = {'cmd': 'bundle exec thin -p 3000'}
        p = serviceparser.Parser('groupname', 'myservice', {'command': ['bundle', 'exec', 'thin', '-p', 3000]})
        p._parse_command('command')
        self.assertEquals(expected, p.app_json)

    def test_parse_command_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_command('command')
        self.assertEquals({}, p.app_json)

    def test_parse_cpu_shares(self):
        expected = {'cpus': 1.0}
        p = serviceparser.Parser('groupname', 'myservice', {'cpu_shares': 1024})
        p._parse_cpu_shares('cpu_shares')
        self.assertEquals(expected, p.app_json)

    def test_parse_cpu_shares_2(self):
        expected = {'cpus': 0.5}
        p = serviceparser.Parser('groupname', 'myservice', {'cpu_shares': 512})
        p._parse_cpu_shares('cpu_shares')
        self.assertEquals(expected, p.app_json)

    def test_parse_cpu_shares_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_cpu_shares('cpu_shares')
        self.assertEquals({}, p.app_json)

    def test_parse_entrypoint(self):
        expected = {'container': {'docker': {'parameters': [{'key': 'entrypoint', 'value': '/code/entrypoint.sh'}]}}}
        p = serviceparser.Parser('groupname', 'myservice', { 'entrypoint': '/code/entrypoint.sh'})
        p._parse_entrypoint('entrypoint')
        self.assertEquals(expected, p.app_json)

    def test_parse_entrypoint_list(self):
        expected = {'container': {'docker': {'parameters': [{'value': 'php -d zend_extension=/usr/local/lib/php/extensions/no-debug-non-zts-20100525/xdebug.so -d memory_limit=-1 vendor/bin/phpunit', 'key': 'entrypoint'}]}}}
        p = serviceparser.Parser('groupname', 'myservice', {'entrypoint': ['php', '-d', 'zend_extension=/usr/local/lib/php/extensions/no-debug-non-zts-20100525/xdebug.so', '-d', 'memory_limit=-1', 'vendor/bin/phpunit']})
        p._parse_entrypoint('entrypoint')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_entrypoint_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_entrypoint('entrypoint')
        self.assertEquals({}, p.app_json)

    def test_parse_environment_dict(self):
        expected = {'env': {'RACK_ENV': 'development', 'SESSION_SECRET': '', 'SHOW': 'true'}}
        p = serviceparser.Parser('groupname', 'myservice', {'environment': {'RACK_ENV':  'development', 'SHOW': 'true', 'SESSION_SECRET': ''}})
        p._parse_environment('environment')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_environment_list(self):
        expected = {'env': {'RACK_ENV': 'development', 'SESSION_SECRET': '', 'SHOW': 'true'}}
        p = serviceparser.Parser('groupname', 'myservice', {'environment': ['RACK_ENV=development', 'SHOW=true', 'SESSION_SECRETBLAH']})
        p._parse_environment('environment')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_environment_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_environment('environment')
        self.assertEquals({}, p.app_json)

    def test_parse_environment_null(self):
        p = serviceparser.Parser('groupname', 'myservice', {'environment': ['SomeValue']})
        p._parse_environment('environment')
        self.assertEquals({'env': { 'SomeValue': ''}}, p.app_json)

    def test_parse_environment_none_string(self):
        p = serviceparser.Parser('groupname', 'myservice', {'environment': ['SomeValue=None']})
        p._parse_environment('environment')
        self.assertEquals({'env': { 'SomeValue': 'None'}}, p.app_json)

    def test_parse_extra_hosts(self):
        expected = {'container': {'docker': {'parameters': [{'key': 'add-host', 'value': 'somehost:162.242.195.82'}, {'key': 'add-host', 'value': 'otherhost:50.31.209.229'}]}}}
        p = serviceparser.Parser('groupname', 'myservice', {'extra_hosts': ['somehost:162.242.195.82', 'otherhost:50.31.209.229']})
        p._parse_extra_hosts('extra_hosts')
        self.assertEquals(expected, p.app_json)

    def test_parse_extra_hosts_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_extra_hosts('extra_hosts')
        self.assertEquals({}, p.app_json)

    def test_parse_labels_dict(self):
        expected = {'labels': {'com.example.description': 'Accounting webapp', 'com.example.department': 'Finance', 'com.example.label-with-empty-value': ''}}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': {'com.example.description': 'Accounting webapp', 'com.example.department': 'Finance', 'com.example.label-with-empty-value': ''}})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_list(self):
        expected = {'labels': {'com.example.description': 'Accounting webapp', 'com.example.department': 'Finance', 'com.example.label-with-empty-value': ''}}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': ['com.example.description=Accounting webapp', 'com.example.department=Finance', 'com.example.label-with-empty-value']})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_labels('labels')
        self.assertEquals({}, p.app_json)

    def test_parse_labels_healthcheck_dict(self):
        expected = {'healthChecks': [{'portIndex': 5, 'protocol': 'HTTP', 'timeoutSeconds': 20, 'intervalSeconds': 5, 'gracePeriodSeconds': 300, 'maxConsecutiveFailures': 3}]}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': {'com.microsoft.acs.dcos.marathon.healthcheck.portIndex':'5'}})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_healthcheck_dict_true(self):
        expected = {'healthChecks': [{'portIndex': 5, 'protocol': 'HTTP', 'timeoutSeconds': 20, 'intervalSeconds': 5, 'gracePeriodSeconds': 300, 'maxConsecutiveFailures': 3}]}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': {'com.microsoft.acs.dcos.marathon.healthcheck':'true'}})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_healthcheck_dict_cmd(self):
        expected = {'healthChecks': [{'portIndex': 0, 'command': {'value': '/bin/bash blah'}, 'protocol': 'COMMAND', 'timeoutSeconds': 20, 'intervalSeconds': 5, 'gracePeriodSeconds': 300, 'maxConsecutiveFailures': 3}]}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': {'com.microsoft.acs.dcos.marathon.healthcheck.command': '/bin/bash blah'}})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_healthcheck_http_port_index(self):
        expected = {'healthChecks': [{'portIndex': 5, 'protocol': 'HTTP', 'timeoutSeconds': 20, 'intervalSeconds': 5, 'gracePeriodSeconds': 300, 'maxConsecutiveFailures': 3}]}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': ['com.microsoft.acs.dcos.marathon.healthcheck.portIndex=5']})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_healthcheck_tcp(self):
        expected = {'healthChecks': [{'portIndex': 0, 'protocol': 'TCP', 'timeoutSeconds': 20, 'intervalSeconds': 5, 'gracePeriodSeconds': 300, 'maxConsecutiveFailures': 3}]}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': ['com.microsoft.acs.dcos.marathon.healthcheck=true']})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_healthcheck_cmd(self):
        expected = {'healthChecks': [{'portIndex': 0, 'command': {'value': '/bin/bash blah'}, 'protocol': 'COMMAND', 'timeoutSeconds': 20, 'intervalSeconds': 5, 'gracePeriodSeconds': 300, 'maxConsecutiveFailures': 3}]}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': ['com.microsoft.acs.dcos.marathon.healthcheck.command=/bin/bash blah']})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_healthcheck_json(self):
        my_hc = [{
            'portIndex': 0,
            'protocol': 'MYCHECKHEALTHCHECK',
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]
        expected = {'healthChecks': [{'portIndex': 0, 'protocol': 'MYCHECKHEALTHCHECK', 'timeoutSeconds': 20, 'intervalSeconds': 5, 'gracePeriodSeconds': 300, 'maxConsecutiveFailures': 3}]}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': ['com.microsoft.acs.dcos.marathon.healthchecks={}'.format(json.dumps(my_hc))]})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_labels_healthcheck_json_dict(self):
        my_hc = [{
            'portIndex': 0,
            'protocol': 'MYCHECKHEALTHCHECK',
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]
        expected = {'healthChecks': [{'portIndex': 0, 'protocol': 'MYCHECKHEALTHCHECK', 'timeoutSeconds': 20, 'intervalSeconds': 5, 'gracePeriodSeconds': 300, 'maxConsecutiveFailures': 3}]}
        p = serviceparser.Parser('groupname', 'myservice', {'labels': {'com.microsoft.acs.dcos.marathon.healthchecks': '[{"portIndex": 0, "protocol": "myhc", "timeout": 30}]'}})
        p._parse_labels('labels')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_mem_limit_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_mem_limit('mem_limit')
        self.assertEquals({}, p.app_json)

    def test_parse_mem_limit_no_unit(self):
        expected = {'mem': 1.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': 1048576})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_b(self):
        expected = {'mem': 1.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '1048576 B'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_b_no_space(self):
        expected = {'mem': 1.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '1048576B'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_k(self):
        expected = {'mem': 4.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '4096 K'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_k_no_space(self):
        expected = {'mem': 4.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '4096K'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_m(self):
        expected = {'mem': 5.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '5 M'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_m_no_space(self):
        expected = {'mem': 5.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '5M'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_g(self):
        expected = {'mem': 1024.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '1 G'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_g_no_space(self):
        expected = {'mem': 512.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '0.5G'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_mem_limit_zero(self):
        expected = {'mem': 0.0}
        p = serviceparser.Parser('groupname', 'myservice', { 'mem_limit': '0'})
        p._parse_mem_limit('mem_limit')
        self.assertEquals(expected, p.app_json)

    def test_parse_stop_signal_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_stop_signal('stop_signal')
        self.assertEquals({}, p.app_json)

    def test_parse_stop_signal(self):
        expected = {'container': {'docker': {'parameters': [{'key': 'stop-signal', 'value': 'SIGUSR1'}]}}}
        p = serviceparser.Parser('groupname', 'myservice', {'stop_signal': 'SIGUSR1'})
        p._parse_stop_signal('stop_signal')
        self.assertEquals(expected, p.app_json)

    def test_parse_privileged_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_privileged('privileged')
        self.assertEquals({}, p.app_json)

    def test_parse_privileged(self):
        expected = {'container': {'docker':{'privileged': 'true'}}}
        p = serviceparser.Parser('groupname', 'myservice', {'privileged': 'true'})
        p._parse_privileged('privileged')
        self.assertEquals(expected, p.app_json)

    def test_parse_user_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_user('user')
        self.assertEquals({}, p.app_json)

    def test_parse_user(self):
        expected = {'container': {'docker': {'parameters': [{'key': 'user', 'value': 'admin'}]}}}
        p = serviceparser.Parser('groupname', 'myservice', {'user': 'admin'})
        p._parse_user('user')
        self.assertEquals(expected, p.app_json)

    def test_parse_working_dir_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_working_dir('working_dir')
        self.assertEquals({}, p.app_json)

    def test_parse_working_dir(self):
        expected = {'container': {'docker': {'parameters': [{'key': 'work-dir', 'value': '/bin/blah'}]}}}
        p = serviceparser.Parser('groupname', 'myservice', {'working_dir': '/bin/blah'})
        p._parse_working_dir('working_dir')
        self.assertEquals(sorted(expected), sorted(p.app_json))

    def test_parse_image_missing(self):
        p = serviceparser.Parser('groupname', 'myservice', {})
        p._parse_image('image')
        self.assertEquals({}, p.app_json)

    def test_parse_image_missing(self):
        expected = {'container': {'docker': {'image': 'myreg/image:blah'}}}
        p = serviceparser.Parser('groupname', 'myservice', {'image':'myreg/image:blah'})
        p._parse_image('image')
        self.assertEquals(expected, p.app_json)

    def test_compose_file(self):
        test_root = os.path.dirname(os.path.realpath(__file__))
        with open(test_root + '/test_compose_1.yml') as stream:
            compose_data = yaml.load(stream)
            all_apps = {'id': 'mygroup', 'apps': []}
            for service_name, service_info in compose_data['services'].items():
                # Get the app_json for the service
                service_parser = serviceparser.Parser('mygroup', service_name, service_info)
                all_apps['apps'].append(service_parser.get_app_json())

            with open(test_root + '/test_compose_1_expected.json') as json_stream:
                expected_json = json.loads(json_stream.read())
                self.assertEquals(sorted(expected_json), sorted(all_apps))
