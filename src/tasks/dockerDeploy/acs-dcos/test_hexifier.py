import base64
import unittest

import hexifier


class DockerAuthConfigHexifierTests(unittest.TestCase):
    def test_not_none(self):
        h = hexifier.DockerAuthConfigHexifier('myhost', 'myusername', 'mypassword')
        self.assertIsNotNone(h)

    def test_values_set(self):
        h = hexifier.DockerAuthConfigHexifier('myhost', 'myusername', 'mypassword')
        self.assertEquals('myhost', h.registry_host)
        self.assertEquals('myusername', h.registry_username)
        self.assertEquals('mypassword', h.registry_password)

    def test_missing_host(self):
        self.assertRaises(ValueError, hexifier.DockerAuthConfigHexifier, None, 'user', 'pass')

    def test_missing_user(self):
        self.assertRaises(ValueError, hexifier.DockerAuthConfigHexifier, 'host', None, 'pass')

    def test_missing_pass(self):
        self.assertRaises(ValueError, hexifier.DockerAuthConfigHexifier, 'host', 'user', None)

    def test_auth_file_path(self):
        h = hexifier.DockerAuthConfigHexifier('myhost', 'myusername', 'mypassword')
        self.assertEquals('myhost/myusername.tar.gz', h.get_auth_file_path())

    def test_auth_file_name(self):
        h = hexifier.DockerAuthConfigHexifier('myhost', 'myusername', 'mypassword')
        self.assertEquals('myusername.tar.gz', h._get_auth_filename())

    def test_create_config_contents(self):
        expected = {
            "auths": {
                'myhost': {
                    "auth": base64.b64encode('myusername:mypassword')
                }
            }
        }
        h = hexifier.DockerAuthConfigHexifier('myhost', 'myusername', 'mypassword')
        self.assertEquals(expected, h._create_config_contents())
