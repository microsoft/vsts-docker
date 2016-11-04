import json
import logging

import hexifier
import marathon


class DockerRegistry(object):
    """
    Class for working with Docker registry
    """
    EXHIBITOR_VIP = '10.1.0.0:80'
    # TODO (peterj, 10/21/2016): 281451: Update exhibitor image once ACS uses DCOS 1.8
    EXHIBITOR_DATA_IMAGE = 'mindaro/dcos-exhibitor-data:1.5.6'
    EXHIBITOR_SERVICE_ID = '/exhibitor-data'

    def __init__(self, registry_host, registry_username, registry_password, marathon_helper):
        self.registry_host = registry_host
        self.registry_username = registry_username
        self.registry_password = registry_password
        self.marathon_helper = marathon_helper

    def get_registry_auth_url(self):
        """
        Handles creating the exhibitor-data service, docker.tar.gz and returns
        the URL to the docker.tar.gz that can be set as a URI on marathon app
        """
        # If registry_host is not set, we assume we don't need the auth URL
        if not self.registry_host:
            return None

        self._ensure_exhibitor_service()
        auth_config_hexifier = hexifier.DockerAuthConfigHexifier(
            self.registry_host, self.registry_username, self.registry_password)

        hex_string = auth_config_hexifier.hexify()
        return self._upload_auth_info(hex_string, auth_config_hexifier.get_auth_file_path())

    def _upload_auth_info(self, hex_string, endpoint):
        """
        Uploads the auth information (hex string) to Exhibitor
        """
        # PUT the hex_string to exhibitor
        self.marathon_helper.put_request(
            'registries/{}'.format(endpoint),
            put_data=hex_string,
            endpoint='/exhibitor/exhibitor/v1/explorer/znode')

        return 'http://{}/registries/{}'.format(
            self.EXHIBITOR_VIP, endpoint)

    def _get_exhibitor_service_json(self):
        exhibitor_data_json = {
            'id': self.EXHIBITOR_SERVICE_ID,
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
        return exhibitor_data_json

    def _ensure_exhibitor_service(self):
        """
        Checks exhibitor service is running and if is not
        it will deploy it.
        """
        exhibitor_json = self._get_exhibitor_service_json()
        # Check if app exists and deploy it if it doesn't
        app_exists = self.marathon_helper.app_exists(self.EXHIBITOR_SERVICE_ID)
        if not app_exists:
            logging.info('Exhibitor-data service not deployed - deploying it now')
            self.marathon_helper.deploy_app(json.dumps(exhibitor_json))
