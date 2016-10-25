
import base64
import binascii
import json
import os
import tarfile
import tempfile

import marathon


class DockerRegistry(object):
    """
    Class for working with Docker registry
    """
    EXHIBITOR_VIP = '10.1.0.0:80'
    # TODO (peterj, 10/21/2016): 281451: Update exhibitor image once ACS uses DCOS 1.8
    EXHIBITOR_DATA_IMAGE = 'mindaro/dcos-exhibitor-data:1.5.6'

    def __init__(self, registry_host, registry_username, registry_password, acs_info):
        self.registry_host = registry_host
        self.registry_username = registry_username
        self.registry_password = registry_password
        self.marathon_helper = marathon.Marathon(acs_info)

    def get_registry_auth_url(self):
        """
        Handles creating the exhibitor-data service, docker.tar.gz and returns
        the URL to the docker.tar.gz that can be set as a URI on marathon app
        """

        # If registry_host is not set, we assume we don't need the auth URL
        if not self.registry_host:
            return ''

        self._ensure_exhibitor_service()
        config_contents = self._get_config_json()

        root_path = tempfile.mkdtemp()
        config_name = 'config.json'
        config_file = os.path.join(root_path, config_name)
        with open(config_file, 'w') as f:
            json.dump(config_contents, f)

        tar_filename = '{}.tar.gz'.format(self.registry_username)
        tar_file_path = os.path.join(root_path, tar_filename)
        tar = tarfile.open(tar_file_path, 'w:gz')
        tar.add(config_file, os.path.join('.docker', config_name))
        tar.close()

        # Open file as binary and convert it to a hex string
        with open(tar_file_path, 'rb') as tf:
            tar_bytes = tf.read()
            hex_string = binascii.hexlify(bytearray(tar_bytes))

        # PUT the hex_string to exhibitor
        response = self.marathon_helper.put_request(
            'registries/{}/{}'.format(self.registry_host, tar_filename),
            put_data=hex_string,
            endpoint='exhibitor/exhibitor/v1/explorer/znode')

        if response.status_code > 400:
            print response.status_code
            raise Exception('Something went wrong: {}'.format(response.text))

        return 'http://{}/registries/{}/{}'.format(
            self.EXHIBITOR_VIP, self.registry_host, tar_filename)

    def _ensure_exhibitor_service(self):
        """
        Checks exhibitor service is running and if is not
        it will deploy it.
        """
        exhibitor_service_id = '/exhibitor-data'

        exhibitor_data_json = {
            'id': exhibitor_service_id,
            'cpus': 0.01,
            'mem': 32,
            'instances': 1,
            'acceptedResourceRoles': [
                'slave_public'
            ],
            'container': {
                'type': 'DOCKER',
                'docker': {
                    'image': self.EXHIBITOR_DATA_IMAGE,
                    'network': 'BRIDGE',
                    'portMappings': [
                        {
                            'containerPort': 80,
                            'hostPort': 0,
                            'protocol': 'tcp',
                            'name': 'tcp80',
                            'labels': {
                                'VIP_0': self.EXHIBITOR_VIP
                                }
                        }]
                    }
                },
            'healthChecks': [
                {
                    'path': '/',
                    'protocol': 'HTTP',
                    'portIndex': 0,
                    'gracePeriodSeconds': 300,
                    'intervalSeconds': 5,
                    'timeoutSeconds': 20,
                    'maxConsecutiveFailures': 3,
                    'ignoreHttp1xx': False
                    }]
            }

        # Check if app exists and deploy it if it doesn't
        response = self.marathon_helper.get_app(exhibitor_service_id)
        if response.status_code == 404:
            print 'Deploying exhibitor-data service'
            self.marathon_helper.deploy_app(json.dumps(exhibitor_data_json))

    def _get_config_json(self):
        """
        Creates the config.json for docker auth
        """
        if not self.registry_host:
            raise ValueError('registry_host not set')

        if not self.registry_username:
            raise ValueError('registry_username not set')

        if not self.registry_password:
            raise ValueError('registry_password not set')

        return {
            "auths": {
                self.registry_host: {
                    "auth": base64.b64encode(self.registry_username + ':' + self.registry_password)
                }
            }
        }
