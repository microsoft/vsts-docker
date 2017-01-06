import logging
import math
import os
import time
import json

import yaml

import acsclient
from kubernetes import Kubernetes
import serviceparser


class DockerComposeParser(object):

    def __init__(self, compose_file, cluster_info, registry_info, group_info,
                 minimum_health_capacity):

        self.cleanup_needed = False
        self._ensure_docker_compose(compose_file)
        with open(compose_file, 'r') as compose_stream:
            self.compose_data = yaml.load(compose_stream)

        self.cluster_info = cluster_info
        self.registry_info = registry_info
        self.group_info = group_info

        self.minimum_health_capacity = minimum_health_capacity

        self.acs_client = acsclient.ACSClient(self.cluster_info)
        self.kubernetes = Kubernetes(self.acs_client)

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
        Parses the docker-compose file and returns the initial marathon.json file
        """
        all_deployments = []
        for service_name, service_info in self.compose_data['services'].items():
            service_parser = serviceparser.Parser(
                self.group_info, self.registry_info, service_name, service_info)
            deployment_json = service_parser.get_deployment_json()
            service_json = service_parser.get_service_json()
            ingress_json = service_parser.get_ingress_json()

            all_deployments.append({
                'deployment_json': deployment_json,
                'service_json': service_json,
                'ingress_json': ingress_json})

        return all_deployments

    def _cleanup(self):
        """
        Removes the group we were trying to deploy in case exception occurs
        """
        if not self.cleanup_needed:
            self._shutdown()
            return

        try:
            group_id = self.group_info.get_id()
            logging.info('Removing "%s".', group_id)
            # self.marathon_helper.delete_group(group_id)
        except Exception as remove_exception:
            raise remove_exception
        finally:
            self._shutdown()

    def _predeployment_check(self):
        """
        Checks if services can be deployed and
        returns True if services are being updated or
        False if this is the first deployment
        """
        group_id = self.group_info.get_id(include_version=False)
        group_version = self.group_info.get_version()
        namespaces = self.kubernetes.get_namespaces('group_id={}'.format(group_id))
        is_update = False
        existing_namespace = None

        if len(namespaces) > 1:
            raise Exception('Another deployment is already in progress')

        if len(namespaces) == 1:
            # Make sure that the version we are trying to deploy
            # is different from the version that's already deployed
            namespaces_with_version = self.kubernetes.get_namespaces(
                'group_id={}&group_version={}'.format(group_id, group_version))
            if len(namespaces_with_version) > 0:
                raise Exception('App with the same version already deployed')
            else:
                is_update = True
                print 'NAMESPACES WITH VERSION: ', namespaces_with_version
                # TODO: Return a tuple here with existing group_id and existing group_version

        if len(namespaces) == 0:
            # Create a new namespace
            labels = {"group_id": group_id, "group_version": group_version}
            logging.info('Creating namespace "%s"', self.group_info.name)
            self.kubernetes.create_namespace(self.group_info.name, labels)

        return is_update

    def _deploy_registry_secret(self):
        """
        Deploys the registry secret
        """
        namespace = self.group_info.name

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


    def deploy(self):
        """
        Deploys the services defined in docker-compose.yml file
        """
        is_update = self._predeployment_check()

        if is_update:
            raise Exception('NOT SUPPORTED YET!')

        self._deploy_registry_secret()

        all_deployments = self._parse_compose()
        namespace = self.group_info.get_id()

        for deployment_item in all_deployments:
            service_json = deployment_item['service_json']
            if service_json:
                self.kubernetes.create_service(service_json, namespace)

            deployment_json = deployment_item['deployment_json']
            self.kubernetes.create_deployment(deployment_json, namespace)

            ingress_json = deployment_item['ingress_json']
            if ingress_json:
                self.kubernetes.create_ingress(ingress_json, namespace)
