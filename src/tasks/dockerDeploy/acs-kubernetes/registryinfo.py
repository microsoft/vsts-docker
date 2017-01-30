import base64
import json


class RegistryInfo(object):
    """
    Holds info about the Docker registry
    """

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def get_secret_name(self):
        """
        Gets the value used for the secret name
        """
        return self.host

    def create_secret_json(self):
        """
        Creates the JSON with Kubernetes secret object
        """
        return json.dumps({
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": self.host
            },
            "data": {
                ".dockerconfigjson": self._get_encoded_config()
            },
            "type": "kubernetes.io/dockerconfigjson"
        })

    def _get_encoded_config(self):
        """
        Gets the config.json contents as an base64 encoded string
        """
        config = {
            "auths": {
                self.host: {
                    "auth": base64.b64encode(self.username + ':' + self.password)
                }
            }
        }
        return base64.b64encode(json.dumps(config))
