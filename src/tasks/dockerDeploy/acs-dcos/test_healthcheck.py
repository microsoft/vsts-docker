import json
import unittest

import healthcheck


class HealthCheckTests(unittest.TestCase):
    def test_not_none(self):
        h = healthcheck.HealthCheck({})
        self.assertIsNotNone(h)

    def test_none_labels(self):
         self.assertRaises(ValueError, healthcheck.HealthCheck, None)

    def test_default_config(self):
        expected = {
            'portIndex': 0,
            'protocol': 'TCP',
            'gracePeriodSeconds': 300,
            'intervalSeconds': 5,
            'timeoutSeconds': 20,
            'maxConsecutiveFailures': 3
        }
        actual = healthcheck.HealthCheck.get_default_health_check_config()
        self.assertEquals(expected, actual)

    def test_label_exists(self):
        labels = {
            'label1':'value1',
            'label2':'value2'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._label_exists('label1')
        self.assertTrue(actual)

    def test_label_exists_empty(self):
        h = healthcheck.HealthCheck({})
        actual = h._label_exists('label1')
        self.assertFalse(actual)

    def test_label_exists_case_sensitive(self):
        labels = {
            'label1':'value1',
            'label2':'value2'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._label_exists('Label1')
        self.assertFalse(actual)

    def test_label_exists_missing(self):
        labels = {
            'label1':'value1',
            'label2':'value2'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._label_exists('MISSING')
        self.assertFalse(actual)

    def test_label_exists_list(self):
        labels = ['label1=value1', 'label2=value2']
        h = healthcheck.HealthCheck(labels)
        actual = h._label_exists('label1')
        self.assertTrue(actual)

    def test_label_exists_none(self):
        labels = ['label1=value1', 'label2=value2']
        h = healthcheck.HealthCheck(labels)
        actual = h._label_exists(None)
        self.assertFalse(actual)

    def test_get_label_value(self):
        labels = {
            'label1':'value1',
            'label2':'value2'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._get_label_value('label1')
        self.assertEquals('value1', actual)

    def test_get_label_value_case_sensitive(self):
        labels = {
            'label1':'value1',
            'label2':'value2'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._get_label_value('LABEL2')
        self.assertEquals(None, actual)

    def test_get_label_value_case_missing(self):
        labels = {
            'label1':'value1',
            'label2':'value2'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._get_label_value('MISSING')
        self.assertEquals(None, actual)

    def test_get_label_value_list(self):
        labels = ['label1=value1', 'label2=value2']
        h = healthcheck.HealthCheck(labels)
        actual = h._get_label_value('label1')
        self.assertEquals('value1', actual)

    def test_get_label_value_none(self):
        labels = {
            'label1':'value1',
            'label2':'value2'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._get_label_value(None)
        self.assertEquals(None, actual)

    def test_set_path_if_exists(self):
        expected = {'path': '/my/path', 'protocol': 'HTTP'}
        labels = {
            healthcheck.HealthCheck.PATH_LABEL:'/my/path'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._set_path_if_exists({})
        self.assertEqual(expected, actual)

    def test_set_path_if_exists_missing(self):
        labels = {
            'something':'/my/path'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._set_path_if_exists({})
        self.assertEqual({}, actual)

    def test_set_port_if_exists(self):
        expected = {'portIndex': '123', 'protocol': 'HTTP'}
        labels = {
            healthcheck.HealthCheck.PORT_INDEX_LABEL: '123'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._set_port_index_if_exists({})
        self.assertEqual(expected, actual)

    def test_set_port_if_exists_missing(self):
        labels = {
            'blah': '123'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._set_port_index_if_exists({})
        self.assertEqual({}, actual)

    def test_set_command_if_exists(self):
        expected = {'protocol': 'COMMAND', 'command': {'value': '/bin/bash something'}}
        labels = {
            healthcheck.HealthCheck.COMMAND_LABEL: '/bin/bash something'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._set_command_if_exists({})
        self.assertEqual(expected, actual)

    def test_set_command_if_exists_missing(self):
        expected = {'protocol': 'COMMAND', 'command': {'value': '/bin/bash something'}}
        labels = {
            'blah': '/bin/bash something'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h._set_command_if_exists({})
        self.assertEqual({}, actual)

    def test_get_health_check_config_tcp(self):
        expected = [{
            'portIndex': 0,
            'protocol': 'TCP',
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]

        labels = {
            healthcheck.HealthCheck.HEALTH_CHECK_LABEL: 'true'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h.get_health_check_config()
        self.assertEquals(expected, actual)

    def test_get_health_check_config_http_portindex(self):
        expected = [{
            'portIndex': 1,
            'protocol': 'HTTP',
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]

        labels = {
            healthcheck.HealthCheck.PORT_INDEX_LABEL: 1
        }
        h = healthcheck.HealthCheck(labels)
        actual = h.get_health_check_config()
        self.assertEquals(expected, actual)

    def test_get_health_check_config_http_path(self):
        expected = [{
            'portIndex': 0,
            'path': '/my/path',
            'protocol': 'HTTP',
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]

        labels = {
            healthcheck.HealthCheck.PATH_LABEL: '/my/path'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h.get_health_check_config()
        self.assertEquals(expected, actual)

    def test_get_health_check_config_http_portindex_path(self):
        expected = [{
            'portIndex': 1,
            'path': '/my/path',
            'protocol': 'HTTP',
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]

        labels = {
            healthcheck.HealthCheck.HEALTH_CHECK_LABEL: True,
            healthcheck.HealthCheck.PORT_INDEX_LABEL: 1,
            healthcheck.HealthCheck.PATH_LABEL: '/my/path'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h.get_health_check_config()
        self.assertEquals(expected, actual)


    def test_get_health_check_config_http_portindex_path_ignore_hc(self):
        expected = [{
            'portIndex': 1,
            'path': '/my/path',
            'protocol': 'HTTP',
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]

        labels = {
            healthcheck.HealthCheck.HEALTH_CHECK_LABEL: True,
            healthcheck.HealthCheck.PORT_INDEX_LABEL: 1,
            healthcheck.HealthCheck.PATH_LABEL: '/my/path'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h.get_health_check_config()
        self.assertEquals(expected, actual)

    def test_get_health_check_config_command(self):
        expected = [{
            'portIndex': 0,
            'protocol': 'COMMAND',
            'command': {'value': '/bin/bash something'},
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]

        labels = {
            healthcheck.HealthCheck.COMMAND_LABEL: '/bin/bash something'
        }
        h = healthcheck.HealthCheck(labels)
        actual = h.get_health_check_config()
        self.assertEquals(expected, actual)

    def test_get_health_check_config_json(self):
        expected = [{
            'portIndex': 0,
            'protocol': 'MYCHECKHEALTHCHECK',
            'timeoutSeconds': 20,
            'intervalSeconds': 5,
            'gracePeriodSeconds': 300,
            'maxConsecutiveFailures': 3}]

        labels = {
            healthcheck.HealthCheck.HEALTH_CHECKS_LABEL: json.dumps(expected)
        }
        h = healthcheck.HealthCheck(labels)
        actual = h.get_health_check_config()
        self.assertEquals(expected, actual)
