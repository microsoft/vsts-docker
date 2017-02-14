import json
import logging
import time


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
        return 'apis/extensions/v1beta1'

    def get_request(self, path, endpoint='api/v1'):
        """
        Makes an HTTP GET request
        """
        return self.acs_client.get_request('{}/{}'.format(endpoint, path.strip('/')))

    def delete_request(self, path, endpoint='api/v1'):
        """
        Makes an HTTP DELETE request
        """
        return self.acs_client.delete_request('{}/{}'.format(endpoint, path.strip('/')))

    def post_request(self, path, post_data, endpoint='api/v1'):
        """
        Makes an HTTP POST request
        """
        return self.acs_client.post_request('{}/{}'.format(endpoint, path.strip('/')),
                                            post_data=post_data)

    def put_request(self, path, put_data=None, endpoint='api/v1', **kwargs):
        """
        Makes an HTTP PUT request
        """
        return self.acs_client.put_request('{}/{}'.format(endpoint, path.strip('/')),
                                           put_data=put_data, **kwargs)

    def create_secret(self, secret_json, namespace):
        """
        Creates a secret on Kubernetes
        """
        logging.debug('Create secret in namespace "%s"', namespace)
        url = 'namespaces/{}/secrets'.format(namespace)
        response = self.post_request(url, post_data=secret_json).json()
        if self._has_failed(response):
            logging.debug(
                'Failed creating a secret in namespace "%s": %s', namespace, response)
            raise Exception(
                'Failed creating a secret in namespace "{}".'.format(namespace))
        return response

    def secret_exists(self, name, namespace):
        """
        Checks if secret exists in a namespace
        """
        logging.debug('Check if secret "%s.%s" exists',
                      name, namespace)
        url = 'namespaces/{}/secrets/{}'.format(
            namespace, name)
        response = self.get_request(url).json()
        return not self._has_failed(response)

    def create_deployment(self, deployment_json, namespace, wait_for_complete=False):
        """
        Creates a deployment on Kubernetes
        """
        logging.debug('Create deployment in namespace "%s"', namespace)
        start_timestamp = time.time()
        url = 'namespaces/{}/deployments'.format(namespace)
        response = self.post_request(
            url, post_data=deployment_json, endpoint=self._beta_endpoint()).json()

        if self._has_failed(response):
            logging.debug(
                'Failed creating a deployment in namespace "%s": %s', namespace, response)
            raise Exception(
                'Failed creating a deployment in namespace "{}".'.format(namespace))

        if wait_for_complete:
            self._wait_for_deployment_complete(
                start_timestamp, namespace, response['metadata']['name'])
        return response

    def deployment_exists(self, name, namespace):
        """
        Checks if deployment exists in a namespace or not
        """
        logging.debug('Check if deployment "%s.%s" exists', name, namespace)
        response = self.get_request(
            'namespaces/{}/deployments/{}'.format(
                namespace, name), self._beta_endpoint()).json()
        return not self._has_failed(response)

    def delete_deployment(self, name, namespace):
        """
        Deletes a deployment
        """
        logging.debug('Delete deployment "%s.%s', name, namespace)
        url = 'namespaces/{}/deployments/{}'.format(namespace, name)
        response = self.delete_request(url).json()
        if self._has_failed(response):
            logging.debug(
                'Failed deleting deployment "%s" from namespace "%s": %s', name, namespace, response)
            raise Exception(
                'Failed deleting deployment "{}" from namespace "{}".', name, namespace)
        return response

    def delete_deployments(self, namespace):
        """
        Deletes all deployments from a namespace
        """
        logging.debug('Delete all deployments from "%s"', namespace)
        url = 'namespaces/{}/deployments'.format(namespace)
        response = self.delete_request(
            url, endpoint=self._beta_endpoint()).json()
        if self._has_failed(response):
            logging.debug(
                'Failed deleting deployments from namespace "%s": %s', namespace, response)
            raise Exception(
                'Failed deleting deployments from namespace "{}".'.format(namespace))
        return response

    def delete_replicasets(self, namespace):
        """
        Deletes all ReplicaSets in a namespace
        """
        logging.debug('Delete replicasets from "%s"', namespace)
        url = 'namespaces/{}/replicasets'.format(namespace)
        response = self.delete_request(
            url, endpoint=self._beta_endpoint()).json()
        if self._has_failed(response):
            logging.debug(
                'Failed deleting replicasets from namespace "%s": %s', namespace, response)
            raise Exception(
                'Failed deleting replicasets from namespace "{}".'.format(namespace))
        return response

    def create_ingress(self, ingress_json, namespace):
        """
        Creates an ingress resource on Kubernetes
        """
        logging.debug('Create ingress in "%s"', namespace)
        url = 'namespaces/{}/ingresses'.format(namespace)
        response = self.post_request(
            url, post_data=ingress_json, endpoint=self._beta_endpoint()).json()
        if self._has_failed(response):
            logging.debug(
                'Failed creating an ingress in namespace "%s": %s', namespace, response)
            raise Exception(
                'Failed creating an ingress in namespace "{}".'.format(namespace))
        return response

    def delete_ingresses(self, namespace):
        """
        Deletes all ingresses from a namespace
        """
        logging.debug('Delete ingresses from namespace "%s"', namespace)
        url = 'namespaces/{}/ingresses'.format(namespace)
        response = self.delete_request(
            url, endpoint=self._beta_endpoint()).json()
        if self._has_failed(response):
            logging.debug(
                'Failed deleting ingresses from namespace "%s": %s', namespace, response)
            raise Exception(
                'Failed deleting ingresses from namespace "{}".'.format(namespace))
        return response

    def create_service(self, service_json, namespace):
        """
        Creates a service on Kubernetes
        """
        logging.debug('Create a service in namespace "%s"', namespace)
        url = 'namespaces/{}/services'.format(namespace)
        response = self.post_request(url, post_data=service_json).json()
        if self._has_failed(response):
            logging.debug(
                'Failed creating service in namespace "%s": %s', namespace, response)
            raise Exception(
                'Failed creating a service in namespace "{}".'.format(namespace))
        return response

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
        response = self.delete_request(url).json()
        if self._has_failed(response):
            logging.debug(
                'Failed deleting service "%s" from namespace "%s": %s', name, namespace, response)
            raise Exception(
                'Failed deleting service "{}" from namespace "{}".'.format(name, namespace))
        return response

    def service_exists(self, name, namespace):
        """
        Checks if service exists in the namespace
        """
        logging.debug('Check if service "%s.%s" exists', name, namespace)
        url = 'namespaces/{}/services/{}'.format(namespace, name)
        response = self.get_request(url).json()
        return not self._has_failed(response)

    def delete_services(self, namespace):
        """
        Deletes all service in specified namespace
        """
        logging.debug('Delete all services from namespace "%s"', namespace)
        url = 'namespaces/{}/services'.format(namespace)
        response = self.get_request(url).json()
        if self._has_failed(response):
            logging.debug('Failed deleting services: %s', response)
            raise Exception(
                'Failed deleting services from namespace "{}".'.format(namespace))
        all_services = response['items']

        for service in all_services:
            service_name = service['metadata']['name']
            logging.debug('Delete service "%s.%s"', service_name, namespace)
            self.delete_service(service_name, namespace)

    def get_namespaces(self, label_selector):
        """
        Gets an array of namespaces based on the label_selector
        """
        response = self.get_request(
            'namespaces?labelSelector={}'.format(label_selector)).json()
        if self._has_failed(response):
            logging.debug('Failed getting namespaces: %s', response)
            raise Exception('Failed getting namespaces.')

        if 'items' in response:
            return response['items']
        return []

    def delete_namespace(self, name):
        """
        Deletes a namespace
        """
        logging.debug('Delete namespace "%s"', name)
        response = self.delete_request('namespaces/{}'.format(name)).json()
        if self._has_failed(response):
            logging.debug('Failed deleting namespace "%s": %s', name, response)
            raise Exception('Failed deleting namespace "{}".'.format(name))
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

        if self._has_failed(response):
            logging.debug('Failed creating namespace "%s": %s', name, response)
            raise Exception('Failed creating namespace "{}".'.format(name))
        return response

    def get_deployment(self, namespace, deployment_name):
        """
        Gets a specific deployment in a namespace
        """
        logging.debug('Get deployment "%s.%s', deployment_name, namespace)
        response = self.get_request(
            'namespaces/{}/deployments/{}'.format(
                namespace, deployment_name), self._beta_endpoint()).json()
        if self._has_failed(response):
            logging.debug('Failed getting deployment "%s" from "%s": %s',
                          deployment_name, namespace, response)
            raise Exception('Failed getting deployment "{}" from namespace "{}".'.format(
                deployment_name, namespace))
        return response

    def get_replicas(self, namespace, deployment_name):
        """
        Gets the number of replicas for a deployment
        """
        logging.debug('Getting replicas for "%s" from "%s".', deployment_name, namespace)
        deployment = self.get_deployment(namespace, deployment_name)
        if 'spec' in deployment:
            if 'replicas' in deployment['spec']:
                return deployment['spec']['replicas']
        raise Exception(
            'Could not find replicas in deployment "{}" from namespace "{}".',
            deployment_name, namespace)

    def _wait_for_deployment_complete(self, start_timestamp, namespace, deployment_name):
        deployment = ''
        deployment_completed = False
        timeout_exceeded = False

        logging.info('Wait for deployment "%s.%s" to complete',
                     deployment_name, namespace)
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
            logging.info('Deployment "%s.%s" completed',
                         deployment_name, namespace)

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
