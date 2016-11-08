import unittest

import mock

from marathon import Marathon
from nginx import LoadBalancerApp


class TestLoadBalancerApp(unittest.TestCase):

    @mock.patch.object(LoadBalancerApp, '_install')
    def test_ensure_exists(self, mock_install):
        marathon_helper_mock = mock.Mock(Marathon)
        compose_data = {'services': {'service-b': {'labels': {'com.microsoft.acs.dcos.marathon.vhost': 'www.contoso.com:80'}}}}
        a = LoadBalancerApp(marathon_helper_mock)
        a.ensure_exists(compose_data)
        self.assertTrue(mock_install.called)

    @mock.patch.object(LoadBalancerApp, '_install')
    def test_ensure_exists_not_called(self, mock_install):
        marathon_helper_mock = mock.Mock(Marathon)
        compose_data = {'services': {'service-b': {'labels': {'mylabel': 'www.contoso.com:80'}}}}
        a = LoadBalancerApp(marathon_helper_mock)
        a.ensure_exists(compose_data)
        self.assertFalse(marathon_helper_mock.ensure_exists.called)
        self.assertFalse(mock_install.called)

    @mock.patch.object(LoadBalancerApp, '_install')
    def test_ensure_exists_vhosts(self, mock_install):
        marathon_helper_mock = mock.Mock(Marathon)
        compose_data = {'services': {'service-b': {'labels': {'com.microsoft.acs.dcos.marathon.vhost': 'www.contoso.com:80'}}}}
        a = LoadBalancerApp(marathon_helper_mock)
        a.ensure_exists(compose_data)
        self.assertTrue(mock_install.called)

    @mock.patch.object(LoadBalancerApp, '_install')
    def test_ensure_exists_install_called_once(self, mock_install):
        marathon_helper_mock = mock.Mock(Marathon)
        compose_data = {'services': {'service-b': {'labels': {'mylabel': 123, 'com.microsoft.acs.dcos.marathon.vhost': 'www.contoso.com:80', 'com.microsoft.acs.dcos.marathon.vhost': 'api.contoso.com:81'}}}}
        a = LoadBalancerApp(marathon_helper_mock)
        a.ensure_exists(compose_data)
        self.assertEquals(1, mock_install.call_count)

    def test_has_external_label_true(self):
        marathon_helper_mock = mock.Mock(Marathon)
        service_info = {'labels': {'mylabel': 123, 'com.microsoft.acs.dcos.marathon.vhost': 'www.contoso.com:80', 'com.microsoft.acs.dcos.marathon.vhost': 'api.contoso.com:81'}}
        a = LoadBalancerApp(marathon_helper_mock)
        self.assertTrue(a._has_external_label(service_info))

    def test_has_external_label_false(self):
        marathon_helper_mock = mock.Mock(Marathon)
        compose_data = {'labels': {'mylabel': 123}}
        a = LoadBalancerApp(marathon_helper_mock)
        self.assertFalse(a._has_external_label(compose_data))
