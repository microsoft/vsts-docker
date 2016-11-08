import hexifier
from exhibitor import Exhibitor


class DockerRegistry(object):
    """
    Class for working with Docker registry
    """
    def __init__(self, registry_host, registry_username, registry_password, marathon_helper):
        self.registry_host = registry_host
        self.registry_username = registry_username
        self.registry_password = registry_password
        self.marathon_helper = marathon_helper
        self.exhibitor_helper = Exhibitor(marathon_helper)

    def get_registry_auth_url(self):
        """
        Handles creating the exhibitor-data service, docker.tar.gz and returns
        the URL to the docker.tar.gz that can be set as a URI on marathon app
        """
        # If registry_host is not set, we assume we don't need the auth URL
        if not self.registry_host:
            return None

        self.marathon_helper.ensure_exists(Exhibitor.APP_ID, Exhibitor.JSON_FILE)
        auth_config_hexifier = hexifier.DockerAuthConfigHexifier(
            self.registry_host, self.registry_username, self.registry_password)

        hex_string = auth_config_hexifier.hexify()
        endpoint = 'registries/{}'.format(auth_config_hexifier.get_auth_file_path())
        return self.exhibitor_helper.upload(hex_string, endpoint)
