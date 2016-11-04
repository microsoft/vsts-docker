import base64
import binascii
import json
import os
import tarfile
import tempfile


class DockerAuthConfigHexifier(object):
    """
    Creates a hex representation of docker.tar.gz file
    that contains config.json with auth information
    """
    CONFIG_FILE_NAME = 'config.json'

    def __init__(self, registry_host, registry_username, registry_password):
        self.registry_host = registry_host
        self.registry_username = registry_username
        self.registry_password = registry_password

        if not self.registry_host:
            raise ValueError('registry_host not set')

        if not self.registry_username:
            raise ValueError('registry_username not set')

        if not self.registry_password:
            raise ValueError('registry_password not set')

    def get_auth_file_path(self):
        """
        Gets the path to the auth file in Exhibitor (e.g. 'hostname/username.tar.gz')
        """
        return '{}/{}'.format(self.registry_host, self._get_auth_filename())

    def hexify(self):
        """
        Create a hex representation of the docker.tar.gz file
        """
        file_path = self._create_temp_auth_file()
        with open(file_path, 'rb') as binary_file:
            file_bytes = binary_file.read()
            hex_string = binascii.hexlify(bytearray(file_bytes))
        return hex_string

    def _get_auth_filename(self):
        """
        Gets the name of the .tar.gz file
        """
        if not self.registry_username:
            raise ValueError('registry_username not set')
        return '{}.tar.gz'.format(self.registry_username)

    def _get_config_filepath(self):
        """
        Gets the full path to the config file
        """
        config_contents = self._create_config_contents()
        root_path = tempfile.mkdtemp()
        config_filepath = os.path.join(root_path, self.CONFIG_FILE_NAME)
        with open(config_filepath, 'w') as config_file:
            json.dump(config_contents, config_file)
        return config_filepath

    def _create_temp_auth_file(self):
        """
        Creates a temporary auth file (.tar.gz) with config.json in .docker folder
        """
        config_filepath = self._get_config_filepath()
        auth_file_path = os.path.join(os.path.dirname(config_filepath), self._get_auth_filename())

        with tarfile.open(auth_file_path, 'w:gz') as tar:
            tar.add(config_filepath, os.path.join('.docker', self.CONFIG_FILE_NAME))
        return auth_file_path

    def _create_config_contents(self):
        """
        Creates the config.json for docker auth
        """
        return {
            "auths": {
                self.registry_host: {
                    "auth": base64.b64encode(self.registry_username + ':' + self.registry_password)
                }
            }
        }
