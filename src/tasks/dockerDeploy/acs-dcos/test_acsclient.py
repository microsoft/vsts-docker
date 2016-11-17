import time
import unittest

import paramiko
import requests
from mock import Mock, patch

import acsclient
import acsinfo


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
    if args[0].startswith('unsupported_version'):
        return MockResponse({'version': '1.2.3'}, 200)
    elif args[0].startswith('supported_version'):
        return MockResponse({'version': '1.8.4'}, 200)
    elif args[0].startswith('missing_version'):
        return MockResponse({'blah': '123'}, 200)
    elif args[0].startswith('wait_for_test'):
        return MockResponse({}, 200)
    elif args[0].startswith('wait_for_test_404'):
        return MockResponse({}, 404)
    elif args[0].startswith('http://make_request_200'):
        return MockResponse({}, 200)
    elif args[0].startswith('http://make_request_404'):
        return MockResponse({}, 404)
    return MockResponse({}, 404)

class AcsClientTest(unittest.TestCase):
    @patch('requests.get', side_effect=mocked_requests_get)
    def test_ensure_dcos_version_unsupported(self, mock_get):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, None, None, 'unsupported_version')
        acs = acsclient.ACSClient(acs_info)
        self.assertRaises(ValueError, acs.ensure_dcos_version)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_ensure_dcos_version_supported(self, mock_get):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, None, None, 'supported_version')
        acs = acsclient.ACSClient(acs_info)
        self.assertTrue(acs.ensure_dcos_version())

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_ensure_dcos_version_missing(self, mock_get):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, None, None, 'missing_version')
        acs = acsclient.ACSClient(acs_info)
        self.assertRaises(Exception, acs.ensure_dcos_version)

    def test_using_direct_connection(self):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, None, None, 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertTrue(acs_client.is_direct)

    def test_using_ssh_connection(self):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, None, None, None)
        acs_client = acsclient.ACSClient(acs_info)
        self.assertFalse(acs_client.is_direct)

    def test_get_private_key_missing(self):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, None, None, 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertRaises(Exception, acs_client._get_private_key)

    def test_get_private_key_invalidkey(self):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, None, 'MYPRIVATEKEY', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertRaises(paramiko.SSHException, acs_client._get_private_key)

    @patch('paramiko.RSAKey')
    def test_get_private_key_called(self, mock_rsakey):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, 'mypassword', 'MYPRIVATEKEY', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        key = acs_client._get_private_key()
        self.assertIsNotNone(key)
        self.assertTrue(mock_rsakey.from_private_key.called)

    def test_setup_tunnel_direct(self):
        acs_info = acsinfo.AcsInfo('myhost', 2200, None, None, None, 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertEquals(acs_client._setup_tunnel_server(), 80)

    @patch('acsclient.ACSClient.get_available_local_port')
    @patch('sshtunnel.SSHTunnelForwarder')
    @patch('sshtunnel.SSHTunnelForwarder.start')
    @patch('acsclient.ACSClient._wait_for_tunnel')
    @patch('acsclient.ACSClient._get_private_key')
    def test_setup_tunnel_ssh(self, mock_get_private_key, mock_wait_for_tunnel, mock_tunnel_forwarder, mock_tunnel, mock_available_port):
        mock_available_port.return_value = '1234'
        mock_get_private_key.return_value = Mock()

        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', None)
        acs_client = acsclient.ACSClient(acs_info)
        return_value = acs_client._setup_tunnel_server()

        self.assertTrue(mock_available_port.called)
        self.assertIsNotNone(acs_client.current_tunnel[0])
        self.assertEquals(acs_client.current_tunnel[1], 1234)
        self.assertTrue(mock_tunnel_forwarder.called)
        self.assertTrue(mock_wait_for_tunnel.called)
        self.assertEquals(return_value, 1234)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_wait_for_tunnel(self, mock_get):
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', None)
        acs_client = acsclient.ACSClient(acs_info)
        self.assertFalse(acs_client.is_running)
        acs_client._wait_for_tunnel(time.time(), 'wait_for_test')
        self.assertTrue(acs_client.is_running)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_wait_for_tunnel_fails(self, mock_get):
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', None)
        acs_client = acsclient.ACSClient(acs_info)
        self.assertRaises(Exception, acs_client._wait_for_tunnel, -1, 'wait_for_test_400')

    @patch('acsclient.ACSClient._setup_tunnel_server')
    def test_get_request_url_ssh(self, mock_tunnel_server):
        mock_tunnel_server.return_value = 1234
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', None)
        acs_client = acsclient.ACSClient(acs_info)
        actual = acs_client._get_request_url('mypath')
        self.assertEquals(actual, 'http://127.0.0.1:1234/mypath')

    @patch('acsclient.ACSClient._setup_tunnel_server')
    def test_get_request_url_direct(self, mock_tunnel_server):
        mock_tunnel_server.return_value = 1234
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)

        actual = acs_client._get_request_url('mypath')
        self.assertEquals(actual, 'http://leader.mesos/mypath')

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.get', side_effect=mocked_requests_get)
    def test_make_request_invalid_method(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_200'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertRaises(Exception, acs_client._make_request, '', 'INVALID')

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.get', side_effect=mocked_requests_get)
    def test_make_request_get_200(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_200'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        
        actual = acs_client._make_request('', 'get')
        self.assertIsNotNone(actual)
        self.assertEquals(actual.status_code, 200)

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.get', side_effect=mocked_requests_get)
    def test_make_request_get_400(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_400'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertRaises(Exception, acs_client._make_request, '', 'get')

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.get', side_effect=mocked_requests_get)
    def test_make_request_get_200_data(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_200'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        
        actual = acs_client._make_request('', 'get', data='mydata')
        self.assertIsNotNone(actual)
        self.assertEquals(actual.status_code, 200)

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.delete', side_effect=mocked_requests_get)
    def test_make_request_delete_200(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_200'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        
        actual = acs_client._make_request('', 'delete')
        self.assertIsNotNone(actual)
        self.assertEquals(actual.status_code, 200)

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.delete', side_effect=mocked_requests_get)
    def test_make_request_delete_400(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_400'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertRaises(Exception, acs_client._make_request, '', 'delete')

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.put', side_effect=mocked_requests_get)
    def test_make_request_put_200(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_200'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        
        actual = acs_client._make_request('', 'put', data='somedata')
        self.assertIsNotNone(actual)
        self.assertEquals(actual.status_code, 200)

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.put', side_effect=mocked_requests_get)
    def test_make_request_put_400(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_400'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertRaises(Exception, acs_client._make_request, '', 'put')

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.post', side_effect=mocked_requests_get)
    def test_make_request_post_200(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_200'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        
        actual = acs_client._make_request('', 'post', data='somedata')
        self.assertIsNotNone(actual)
        self.assertEquals(actual.status_code, 200)

    @patch('acsclient.ACSClient._get_request_url')
    @patch('requests.post', side_effect=mocked_requests_get)
    def test_make_request_post_400(self, mock_get, mock_request_url):
        mock_request_url.return_value = 'http://make_request_400'
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        self.assertRaises(Exception, acs_client._make_request, '', 'post')

    @patch('acsclient.ACSClient._make_request')
    def test_get_request(self, mock_make_request):
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)

        acs_client.get_request('mypath')
        mock_make_request.assert_called_with('mypath', 'get')

    @patch('acsclient.ACSClient._make_request')
    def test_delete_request(self, mock_make_request):
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)

        acs_client.delete_request('mypath')
        mock_make_request.assert_called_with('mypath', 'delete')

    @patch('acsclient.ACSClient._make_request')
    def test_put_request(self, mock_make_request):
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)

        acs_client.put_request('mypath', put_data='mydata')
        mock_make_request.assert_called_with('mypath', 'mypath', 'mydata')

    @patch('acsclient.ACSClient._make_request')
    def test_post_request(self, mock_make_request):
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)

        acs_client.post_request('mypath', post_data='mydata')
        mock_make_request.assert_called_with('mypath', 'mypath', 'mydata')

    @patch('acsclient.ACSClient.current_tunnel')
    def test_shutdown_not_called(self, mock_current_tunnel):
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        acs_client.shutdown()

        self.assertFalse(acs_client.is_running)
        self.assertFalse(mock_current_tunnel[0].stop.called)

    @patch('acsclient.ACSClient.current_tunnel')
    def test_shutdown(self, mock_current_tunnel):
        acs_info = acsinfo.AcsInfo('myhost', 2200, 'user', 'password', 'pkey', 'http://leader.mesos')
        acs_client = acsclient.ACSClient(acs_info)
        acs_client.is_running = True
        acs_client.shutdown()

        self.assertFalse(acs_client.is_running)
        self.assertTrue(mock_current_tunnel[0].stop.called)
