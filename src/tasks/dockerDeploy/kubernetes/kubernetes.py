import json

class Kubernetes(object):
    """
    Class used for working with Kubernetes API 
    """

    def __init__(self, acs_client):
        self.acs_client = acs_client

    def _beta_endpoint(self):
        """
        Gets the beta endpoint
        """
        return '/apis/extensions/v1beta1'

    def get_request(self, path, endpoint='api/v1'):
        """
        Makes an HTTP GET request
        """
        return self.acs_client.get_request('{}/{}'.format(endpoint, path))

    def delete_request(self, path, endpoint='api/v1'):
        """
        Makes an HTTP DELETE request
        """
        return self.acs_client.delete_request('{}/{}'.format(endpoint, path))

    def post_request(self, path, post_data, endpoint='api/v1'):
        """
        Makes an HTTP POST request
        """
        return self.acs_client.post_request('{}/{}'.format(endpoint, path),
                                            post_data=post_data)

    def put_request(self, path, put_data=None, endpoint='api/v1', **kwargs):
        """
        Makes an HTTP PUT request
        """
        return self.acs_client.put_request('{}/{}'.format(endpoint, path),
                                           put_data=put_data, **kwargs)

    def create_secret(self, secret_json, namespace):
        """
        Creates a secret on Kubernetes
        """
        url = 'namespaces/{}/secrets'.format(namespace)
        return self.post_request(url, post_data=secret_json)

    def secret_exists(self, label_selector, namespace):
        """
        Checks if secret defined by label_selector ("name=secret_name") exists or not
        """
        url = 'namespaces/{}/secrets?labelSelector={}'.format(
            namespace, label_selector)
        response = self.get_request(url).json()
        if len(response['items']) == 0:
            return False
        return True

    def create_deployment(self, deployment_json, namespace):
        """
        Creates a deployment on Kubernetes
        """
        url = 'namespaces/{}/deployments'.format(namespace)
        return self.post_request(url, post_data=deployment_json, endpoint=self._beta_endpoint())

    def create_ingress(self, ingress_json, namespace):
        """
        Creates an ingress resource on Kubernetes
        """
        url = 'namespaces/{}/ingresses'.format(namespace)
        return self.post_request(url, post_data=ingress_json, endpoint=self._beta_endpoint())

    def create_service(self, service_json, namespace):
        """
        Creates a service on Kubernetes
        """
        url = 'namespaces/{}/services'.format(namespace)
        return self.post_request(url, post_data=service_json)

    def namespace_exists(self, label_selector):
        """
        Checks if a namespace defined by the label_selector exists or not
        """
        response = self.get_request(
            'namespaces?labelSelector={}'.format(label_selector)).json()
        if len(response['items'] == 0):
            return False
        return True

    def get_namespaces(self, label_selector):
        """
        Gets an array of namespaces based on the label_selector
        """
        response = self.get_request(
            'namespaces?labelSelector={}'.format(label_selector)).json()
        return response['items']

    def create_namespace(self, name, labels):
        """
        Creates a new namespace
        """
        namespace_json = {
            "kind": "Namespace",
            "apiVersion": "v1",
            "metadata": {
                "name": name,
                "labels": labels
            }
        }

        return self.post_request('namespaces', post_data=json.dumps(namespace_json)).json()
