
import os
import json
import logging
import time


class IngressController(object):
    """
    This class takes care of deploying Nginx Ingress load balancer
    and default backend for the load balancer

    Deploying this will expose an IP on Azure load balancer.
    """

    # Sadly, it can take 5 minutes or more for
    # Azure to open up a port on LB
    external_ip_max_wait_time = 10 * 60

    DEFAULT_NAMESPACE = 'default'
    DEFAULT_BACKEND_DEPLOYMENT_FILE = 'ingress/default-backend.json'
    DEFAULT_BACKEND_SERVICE_FILE = 'ingress/default-backend-svc.json'
    NGINX_INGRESS_DEPLOYMENT_FILE = 'ingress/nginx-ingress-lb.json'
    NGINX_INGRESS_SERVICE_FILE = 'ingress/nginx-ingress-lb-svc.json'

    DEFAULT_BACKEND_NAME = 'default-http-backend'
    NGINX_INGRESS_LB_NAME = 'nginx-ingress-controller'

    def __init__(self, kubernetes):
        self.kubernetes = kubernetes

    def deploy(self, wait_for_external_ip=False):
        """
        Deploys the default backend and Nginx Ingress load balacer
        if needed
        """
        start_timestamp = time.time()
        logging.info('Deploying default backend')
        self._ensure_default_backend()
        logging.info('Deploying Nginx Ingress Load balancer')
        self._ensure_nginx_ingress_lb()

        if wait_for_external_ip:
            self._wait_for_external_ip(start_timestamp)

    def get_external_ip(self):
        """
        Gets the ExternalIP where the Nginx loadbalacer is exposed on
        """
        service = self.kubernetes.get_service(
            IngressController.NGINX_INGRESS_LB_NAME, IngressController.DEFAULT_NAMESPACE)
        external_ip = None

        try:
            external_ip = service['status']['loadBalancer']['ingress'][0]['ip']
        except KeyError:
            logging.debug('Error getting [status][loadBalancer][ingress]')
            return None

        return external_ip

    def _wait_for_external_ip(self, start_timestamp):
        """
        Waits for the external IP to become active
        """
        ip_obtained = False
        timeout_exceeded = False

        logging.info('Waiting for ExternalIP')
        while not ip_obtained:
            if self._wait_time_exceeded(self.external_ip_max_wait_time, start_timestamp):
                timeout_exceeded = True
                break
            external_ip = self.get_external_ip()

            if external_ip:
                ip_obtained = True
                break
            time.sleep(1)

        if timeout_exceeded:
            raise Exception('Timeout exceeded waiting for ExternalIP')

        if ip_obtained:
            logging.info('ExternalIP obtained')

    def _ensure_default_backend(self):
        """
        Ensures default backed deployment and
        service are deployed
        """
        self._ensure_service(IngressController.DEFAULT_BACKEND_NAME,
                             IngressController.DEFAULT_NAMESPACE,
                             IngressController.DEFAULT_BACKEND_SERVICE_FILE)
        self._ensure_deployment(IngressController.DEFAULT_BACKEND_NAME,
                                IngressController.DEFAULT_NAMESPACE,
                                IngressController.DEFAULT_BACKEND_DEPLOYMENT_FILE)

    def _ensure_nginx_ingress_lb(self):
        """
        Ensures NGINX ingress loadbalancer deployment and
        service are deployed
        """
        self._ensure_service(IngressController.NGINX_INGRESS_LB_NAME,
                             IngressController.DEFAULT_NAMESPACE,
                             IngressController.NGINX_INGRESS_SERVICE_FILE)
        self._ensure_deployment(IngressController.NGINX_INGRESS_LB_NAME,
                                IngressController.DEFAULT_NAMESPACE,
                                IngressController.NGINX_INGRESS_DEPLOYMENT_FILE)

    def _ensure_service(self, name, namespace, json_file):
        """
        Ensures service exists and if not it deploys it
        """
        if not self.kubernetes.service_exists(name, namespace):
            logging.info('Deploying "%s" service', name)
            service_json = self._load_json_from_file(json_file)
            self.kubernetes.create_service(
                json.dumps(service_json), namespace)

    def _ensure_deployment(self, name, namespace, json_file):
        """
        Ensures deployment exists and if not it deploys it
        """
        if not self.kubernetes.deployment_exists(name, namespace):
            logging.info('Creating deployment "%s"', name)
            service_json = self._load_json_from_file(json_file)
            self.kubernetes.create_deployment(
                json.dumps(service_json), namespace, wait_for_complete=True)

    def _load_json_from_file(self, file_path):
        """
        Gets json contents from a file
        """
        full_path = os.path.join(os.getcwd(), file_path)
        with open(full_path) as json_file:
            data = json.load(json_file)
        return data

    def _wait_time_exceeded(self, max_wait, timestamp):
        """
        Checks if the wait time was exceeded.
        """
        return time.time() - timestamp > max_wait
