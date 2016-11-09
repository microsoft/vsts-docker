import unittest

import requests
from mock import patch

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
