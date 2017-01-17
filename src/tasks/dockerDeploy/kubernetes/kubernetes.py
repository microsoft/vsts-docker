import json
import time
import logging

class Kubernetes(object):
    """
    Class used for working with Kubernetes API
    """
    deployment_max_wait_time = 5 * 60

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
        logging.debug('Create secret in namespace "%s"', namespace)
        url = 'namespaces/{}/secrets'.format(namespace)
        response = self.post_request(url, post_data=secret_json).json()
        return response

    def secret_exists(self, label_selector, namespace):
        """
        Checks if secret defined by label_selector ("name=secret_name") exists or not
        """
        logging.debug('Check if secret in namespace "%s" with selector "%s" exists',
                      namespace, label_selector)
        url = 'namespaces/{}/secrets?labelSelector={}'.format(
            namespace, label_selector)
        response = self.get_request(url).json()
        if len(response['items']) == 0:
            logging.debug('\tSecret does not exist')
            return False
        
        logging.debug('\tSecret exists')
        return True

    def create_deployment(self, deployment_json, namespace, wait_for_complete=False):
        """
        Creates a deployment on Kubernetes
        """
        logging.debug('Create deployment in namespace "%s"', namespace)
        start_timestamp = time.time()
        url = 'namespaces/{}/deployments'.format(namespace)
        response = self.post_request(
            url, post_data=deployment_json, endpoint=self._beta_endpoint()).json()

        if wait_for_complete:
            self._wait_for_deployment_complete(
                start_timestamp, namespace, response['metadata']['name'])
        return response

    def deployment_exists(self, name, namespace):
        """
        Checks if deployment exists in a namespace or not
        """
        logging.debug('Check if deployment "%s.%s" exists', name, namespace)
        response = self.get_deployment(namespace, name)
        if self._has_failed(response):
            logging.debug('\tDeployment "%s.%s" does not exists', name, namespace)
            return False
        if response['kind'] == 'Deployment':
            logging.debug('\tDeployment "%s.%s" exists', name, namespace)
            return True
        raise ValueError('Unknown response kind: "%s"', response)

    def delete_deployment(self, name, namespace):
        """
        Deletes a deployment
        """
        logging.debug('Delete deployment "%s.%s', name, namespace)
        url = 'namespaces/{}/deployments/{}'.format(namespace, name)
        response = self.delete_request(url)
        return response

    def delete_deployments(self, namespace):
        """
        Deletes all deployments from a namespace
        """
        logging.debug('Delete all deployments from "%s"', namespace)
        url = 'namespaces/{}/deployments'.format(namespace)
        response = self.delete_request(url, endpoint=self._beta_endpoint()).json()
        return response

    def delete_replicasets(self, namespace):
        """
        Deletes all ReplicaSets in a namespace
        """
        logging.debug('Delete replicasets from "%s"', namespace)
        url = 'namespaces/{}/replicasets'.format(namespace)
        return  self.delete_request(url, endpoint=self._beta_endpoint())

    def create_ingress(self, ingress_json, namespace):
        """
        Creates an ingress resource on Kubernetes
        """
        logging.debug('Create ingress in "%s"', namespace)
        url = 'namespaces/{}/ingresses'.format(namespace)
        return self.post_request(url, post_data=ingress_json, endpoint=self._beta_endpoint())

    def delete_ingresses(self, namespace):
        """
        Deletes all ingresses from a namespace
        """
        logging.debug('Delete ingresses from namespace "%s"', namespace)
        url = 'namespaces/{}/ingresses'.format(namespace)
        return self.delete_request(url, endpoint=self._beta_endpoint())

    def create_service(self, service_json, namespace):
        """
        Creates a service on Kubernetes
        """
        logging.debug('Create a service in namespace "%s"', namespace)
        url = 'namespaces/{}/services'.format(namespace)
        return self.post_request(url, post_data=service_json)

    def get_service(self, name, namespace):
        """
        Gets the service
        """
        logging.debug('Get service "%s.%s"', name, namespace)
        url = 'namespaces/{}/services/{}'.format(namespace, name)
        return self.get_request(url).json()

    def delete_service(self, name, namespace):
        """
        Deletes a service in specified namespace
        """
        logging.debug('Delete service "%s.%s"', name, namespace)
        url = 'namespaces/{}/services/{}'.format(namespace, name)
        return self.delete_request(url)

    def service_exists(self, name, namespace):
        """
        Checks if service exists in the namespace
        """
        logging.debug('Check if service "%s.%s" exists', name, namespace)
        url = 'namespaces/{}/services/{}'.format(namespace, name)
        response = self.get_request(url).json()
        if self._has_failed(response):
            logging.debug('\tService "%s.%s" does not exist', name, namespace)
            return False

        if response['kind'] == 'Service':
            logging.debug('\tService "%s.%s" exists', name, namespace)
            return True

        raise ValueError('Unknown response kind: "%s"', response)

    def delete_services(self, namespace):
        """
        Deletes all service in specified namespace
        """
        logging.debug('Delete all services from namespace "%s"', namespace)
        url = 'namespaces/{}/services'.format(namespace)
        response = self.get_request(url).json()
        all_services = response['items']

        for service in all_services:
            service_name = service['metadata']['name']
            logging.debug('Delete service "%s.%s"', service_name, namespace)
            self.delete_service(service_name, namespace)

    def namespace_exists(self, label_selector):
        """
        Checks if a namespace defined by the label_selector exists or not
        """
        logging.debug('Check if namespace with selector "%s" exists', label_selector)
        response = self.get_request(
            'namespaces?labelSelector={}'.format(label_selector)).json()
        if len(response['items'] == 0):
            logging.debug('\tNamespace with selector "%s" does not exist', label_selector)
            return False

        logging.debug('\tNamespace with selector "%s" exists', label_selector)
        return True

    def get_namespaces(self, label_selector):
        """
        Gets an array of namespaces based on the label_selector
        """
        response = self.get_request(
            'namespaces?labelSelector={}'.format(label_selector)).json()
        return response['items']

    def delete_namespace(self, name):
        """
        Deletes a namespace
        """
        logging.debug('Delete namespace "%s"', name)
        response = self.delete_request(
            'namespaces?labelSelector=name={}'.format(name)).json()
        return response

    def create_namespace(self, name, labels):
        """
        Creates a new namespace
        """
        logging.debug('Create namespace "%s"', name)
        namespace_json = {
            "kind": "Namespace",
            "apiVersion": "v1",
            "metadata": {
                "name": name,
                "labels": labels
            }
        }

        response = self.post_request(
            'namespaces', post_data=json.dumps(namespace_json)).json()
        return response

    def get_deployment(self, namespace, deployment_name):
        """
        Gets a specific deployment in a namespace
        """
        logging.debug('Get deployment "%s.%s', deployment_name, namespace)
        response = self.get_request(
            'namespaces/{}/deployments/{}'.format(
                namespace, deployment_name), self._beta_endpoint())
        return response.json()

    def get_replicas(self, namespace, deployment_name):
        """
        Gets the number of replicas for a deployment
        """
        deployment = self.get_deployment(namespace, deployment_name)
        return deployment['spec']['replicas']

    def _wait_for_deployment_complete(self, start_timestamp, namespace, deployment_name):
        deployment = ''
        deployment_completed = False
        timeout_exceeded = False

        logging.info('Wait for deployment "%s.%s" to complete', namespace, deployment_name)
        while not deployment_completed:
            if self._wait_time_exceeded(self.deployment_max_wait_time, start_timestamp):
                timeout_exceeded = True
                break

            deployment = self.get_deployment(namespace, deployment_name)
            status = deployment['status']

            if not status or 'observedGeneration' not in status or 'updatedReplicas' not in status:
                time.sleep(1)
                continue

            if (status['observedGeneration'] >= deployment['metadata']['generation']) and\
               (status['updatedReplicas'] == deployment['spec']['replicas']):
                deployment_completed = True
                break
            time.sleep(1)

        if timeout_exceeded:
            raise Exception(
                'Timeout exceeded waiting for deployment to complete')

        if deployment_completed:
            logging.info('Deployment "%s.%s" completed', namespace, deployment_name)

    def _wait_time_exceeded(self, max_wait, timestamp):
        """
        Checks if the wait time was exceeded.
        """
        return time.time() - timestamp > max_wait

    def _has_failed(self, response):
        """
        Checks if the response failed (404) or not
        """
        if response['kind'] == 'Status':
            if 'code' in response and response['code'] == 404:
                return True
        return False
