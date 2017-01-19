import logging
import math
import os
import time
import json

import yaml

import acsclient
from kubernetes import Kubernetes
import serviceparser
from ingress_controller import IngressController


class DockerComposeParser(object):

    def __init__(self, compose_file, cluster_info, registry_info, group_info):

        self.cleanup_needed = False
        self._ensure_docker_compose(compose_file)
        with open(compose_file, 'r') as compose_stream:
            self.compose_data = yaml.load(compose_stream)

        self.cluster_info = cluster_info
        self.registry_info = registry_info
        self.group_info = group_info

        self.acs_client = acsclient.ACSClient(self.cluster_info)
        self.kubernetes = Kubernetes(self.acs_client)
        self.ingress_controller = IngressController(self.kubernetes)

    def __enter__(self):
        """
        Used when entering the 'with'
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called when exiting the 'with' block
        """
        if not exc_type is SystemExit:
            self._cleanup()
        else:
            self._shutdown()

    def _shutdown(self):
        """
        Shuts down the acs client if needed
        """
        if self.acs_client:
            self.acs_client.shutdown()

    def _ensure_docker_compose(self, docker_compose_file):
        """
        1. Raises an error if there is no docker_compose_file present.
        2. Raises an error if the version specified in the docker_compose_file is not
        docker_compose_version.
        """
        docker_compose_expected_version = '2'
        if not os.path.isfile(docker_compose_file):
            raise Exception(
                'Docker compose file "{}" was not found.'.format(docker_compose_file))
        with open(docker_compose_file, 'r') as f:
            compose_data = yaml.load(f)
            if 'services' not in compose_data.keys():
                raise ValueError(
                    'Docker compose file "{}" is missing services information.'.format(
                        docker_compose_file))
            if 'version' not in compose_data.keys():
                raise ValueError(
                    'Docker compose file "{}" is missing version information.'.format(
                        docker_compose_file))
            if not docker_compose_expected_version in compose_data['version']:
                raise ValueError(
                    'Docker compose file "{}" has incorrect version. \
                    Only version "{}" is supported.'.format(
                        docker_compose_file,
                        docker_compose_expected_version))

    def _parse_compose(self):
        """
        Parses the docker-compose file and returns the list of all deployments
        """
        all_deployments = []
        needs_ingress_controller = False
        for service_name, service_info in self.compose_data['services'].items():
            service_parser = serviceparser.Parser(
                self.group_info, self.registry_info, service_name, service_info)
            deployment_json = service_parser.get_deployment_json()
            service_json = service_parser.get_service_json()
            ingress_json = service_parser.get_ingress_json()

            # Check if need to deploy ingress controller or not
            if not needs_ingress_controller:
                needs_ingress_controller = service_parser.needs_ingress_controller

            all_deployments.append({
                'service_name': service_name,
                'deployment': {'json': deployment_json},
                'service': {'json': service_json},
                'ingress': {'json': ingress_json}
            })

        return needs_ingress_controller, all_deployments

    def _cleanup(self):
        """
        Removes the group we were trying to deploy in case exception occurs
        """
        if not self.cleanup_needed:
            self._shutdown()
            return

        try:
            namespace = self.group_info.get_namespace()
            logging.info('Removing all resources from namespace "%s".', namespace)
            self._delete_all(namespace)
        except Exception as remove_exception:
            raise remove_exception
        finally:
            self._shutdown()

    def _create_namespace(self, group_info):
        """
        Creates a new namespace
        """
        labels = {
            "group_id": group_info.get_id(include_version=False),
            "group_version": group_info.version,
            "name": group_info.get_namespace()
        }
        logging.info('Creating namespace "%s"', group_info.get_namespace())
        self.kubernetes.create_namespace(group_info.get_namespace(), labels)

    def _predeployment_check(self):
        """
        Checks if services can be deployed and
        returns True if services are being updated or
        False if this is the first deployment
        """
        group_id = self.group_info.get_id(include_version=False)
        namespaces = self.kubernetes.get_namespaces(
            'group_id={}'.format(group_id))
        group_version = self.group_info.get_version()
        is_update = False

        if len(namespaces) > 1:
            raise Exception('Another deployment is already in progress')

        if len(namespaces) == 1:
            # There is one namespace with the group_id already deployed
            # we need to check the version to see if it's an update
            deployed_version = namespaces[0][
                'metadata']['labels']['group_version']
            if deployed_version == group_version:
                raise Exception('App with the same version already deployed')
            else:
                # This version is not deployed yet, so we are doing an update
                is_update = True
                existing_namespace = namespaces[0]['metadata']['name']
                return (is_update, deployed_version, existing_namespace)

        return (is_update, None, None)

    def _deploy_registry_secret(self):
        """
        Deploys the registry secret
        """
        namespace = self.group_info.get_namespace()

        # TODO: Could registry be global; otherwise we are going to deploy
        # the secret on each service deployment because of a different
        # namespace
        registry_secret = self.registry_info.create_secret_json()
        if not self.kubernetes.secret_exists('name={}'.format(
                self.registry_info.get_secret_name()), namespace):
            logging.info('Deploying registry secret')
            self.kubernetes.create_secret(registry_secret, namespace)
        else:
            logging.info('Registry secret already exists')

    def _delete_all(self, namespace):
        """
        Deletes all resources from the specified namespace
        """
        self.kubernetes.delete_ingresses(namespace)
        self.kubernetes.delete_services(namespace)
        self.kubernetes.delete_deployments(namespace)
        self.kubernetes.delete_replicasets(namespace)
        self.kubernetes.delete_namespace(namespace)

    def deploy(self):
        """
        Deploys the services defined in docker-compose.yml file
        """
        new_namespace = self.group_info.get_namespace()
        is_update, _, existing_namespace = self._predeployment_check()

        # Create a new namespace - it's either a first deployment or an upgrade
        self._create_namespace(self.group_info)
        self.cleanup_needed = True

        self._deploy_registry_secret()
        needs_ingress_controller, all_deployments = self._parse_compose()

        if needs_ingress_controller:
            # Deploy Ingress controller if it's not running yet
            self.ingress_controller.deploy(wait_for_external_ip=True)
            logging.info('NGINX Ingress Loadbalancer deployed')
        else:
            logging.info('Skipping NGINX Ingress Loadbalancer deployment')

        if is_update:
            for deployment_item in all_deployments:
                service_name = deployment_item['service_name']
                existing_replicas = self.kubernetes.get_replicas(
                    existing_namespace, service_name)
                logging.info('Update replicas for "%s" to "%s"',
                             service_name, existing_replicas)
                deployment_json = json.loads(
                    deployment_item['deployment']['json'])
                deployment_json['spec']['replicas'] = existing_replicas

                # Create the deployment
                self.kubernetes.create_deployment(
                    json.dumps(deployment_json), new_namespace, wait_for_complete=True)

                # Create the service
                service_json = deployment_item['service']['json']
                if service_json:
                    self.kubernetes.create_service(service_json, new_namespace)

                # Create ingress
                ingress_json = deployment_item['ingress']['json']
                if ingress_json:
                    self.kubernetes.create_ingress(ingress_json, new_namespace)

            logging.info('Remove previous deployment')
            self._delete_all(existing_namespace)
        else:
            for deployment_item in all_deployments:
                service_json = deployment_item['service']['json']
                if service_json:
                    self.kubernetes.create_service(service_json, new_namespace)

                deployment_json = deployment_item['deployment']['json']
                self.kubernetes.create_deployment(
                    deployment_json, new_namespace)

                ingress_json = deployment_item['ingress']['json']
                if ingress_json:
                    self.kubernetes.create_ingress(ingress_json, new_namespace)

        if needs_ingress_controller:
            logging.info(
                'ExternalIP of NGINX Ingress Loadbalancer: "%s"',
                self.ingress_controller.get_external_ip())
        logging.info('Deployment completed')
