import json
import logging
import os
import re
import threading
import time

from marathon_deployments import DeploymentMonitor
from mesos import Mesos


class Marathon(object):
    """
    Class used for working with Marathon API
    """
    # Max time to wait (in seconds) for deployments to complete
    deployment_max_wait_time = 5 * 60

    def __init__(self, acs_client):
        self.acs_client = acs_client
        self.mesos = Mesos(self.acs_client)

    def get_url(self, path):
        """
        Gets the URL to Marathon
        """
        return self.acs_client.create_request_url(path, 80)

    def get_request(self, path, endpoint='service/marathon/v2'):
        """
        Makes an HTTP GET request
        """
        return self.acs_client.get_request('{}/{}'.format(endpoint, path))

    def delete_request(self, path, endpoint='service/marathon/v2'):
        """
        Makes an HTTP DELETE request
        """
        return self.acs_client.delete_request('{}/{}'.format(endpoint, path))

    def post_request(self, path, post_data, endpoint='service/marathon/v2'):
        """
        Makes an HTTP POST request
        """
        return self.acs_client.post_request('{}/{}'.format(endpoint, path),
                                            post_data=post_data)

    def put_request(self, path, put_data=None, endpoint='service/marathon/v2', **kwargs):
        """
        Makes an HTTP PUT request
        """
        return self.acs_client.put_request('{}/{}'.format(endpoint, path),
                                           put_data=put_data, **kwargs)

    def delete_group(self, group_id, force=None):
        """
        Deletes a group from marathon and returns true if the call was successfull
        """
        if not group_id:
            raise ValueError('group_id not provided')

        if force is None:
            force = True

        response = self.delete_request('groups/{}?force={}'.format(group_id, force))
        return response

    def get_deployments(self):
        """
        Gets all deployments from Marathon
        """
        return self.get_request('deployments')

    def app_exists(self, app_id):
        """
        Checks if app with the provided ID exists
        """
        all_apps = self.get_request('apps').json()

        if not 'apps' in all_apps:
            return False

        for app in all_apps['apps']:
            if app['id'] == app_id:
                return True
        return False

    def ensure_exists(self, app_id, json_file):
        """
        Checks if app with provided ID is deployed on Marathon and
        deploys it if it is not
        """
        logging.info('Check if app "%s" is deployed', app_id)
        app_exists = self.app_exists(app_id)
        if not app_exists:
            logging.info('Deploying app "%s"', app_id)
            json_contents = self._load_json(json_file)
            self.deploy_app(json.dumps(json_contents))

    def _load_json(self, file_path):
        """
        Loads contents of a JSON file and returns it
        """
        file_path = os.path.join(os.getcwd(), file_path)
        with open(file_path) as json_file:
            data = json.load(json_file)
        return data

    def deploy_app(self, app_json):
        """
        Deploys an app to marathon
        """
        if not app_json:
            raise ValueError('app_json not provided')

        start_timestamp = time.time()
        response = self.post_request('apps', post_data=app_json)
        self._wait_for_deployment_complete(response, start_timestamp)

    def update_group(self, marathon_json):
        """
        Updates an existing marathon group
        """
        return self._deploy_group(marathon_json, 'PUT')

    def deploy_group(self, marathon_json):
        """
        Deploys a new marathon group
        """
        return self._deploy_group(marathon_json, 'POST')

    def _deploy_group(self, marathon_json, method):
        """
        Creates and starts a new application group defined in marathon_json
        """
        if not marathon_json:
            raise ValueError('marathon_json not provided')

        start_timestamp = time.time()
        if method == 'POST':
            response = self.post_request('groups', json.dumps(marathon_json))
        elif method == 'PUT':
            response = self.put_request('groups', put_data=json.dumps(marathon_json))
        else:
            raise ValueError('Invalid method "{}"'.format(method))

        self._wait_for_deployment_complete(response, start_timestamp)
        return response

    def _get_all_group_ids(self, data):
        """
        Recursively gets all group Ids
        """
        for group in data:
            for k, value in group.items():
                if k == 'id':
                    yield value
                elif k == 'groups':
                    for val in self._get_all_group_ids(value):
                        yield val

    def get_group_ids(self, prefix):
        """
        Gets the list of all group IDs deployed in Marathon,
        that start with the provided prefix
        """
        # We only get group IDs
        response = self.get_request('groups?embed=group.groups').json()
        all_groups = self._get_all_group_ids([response])
        return [group for group in all_groups if group.startswith(prefix)]

    def get_group(self, group_id):
        """
        Gets the group with the provided group_id
        """
        group_id = self.get_group_ids(group_id)[0]

        response = self.get_request('groups/{}'.format(group_id)).json()
        return response

    def scale_group(self, group_id, scale_factor, log_failures=True):
        """
        Scales the group for provided scale_factor
        """
        start_timestamp = time.time()
        response = self.put_request('groups/{}'.format(group_id), json={'scaleBy': scale_factor})
        self._wait_for_deployment_complete(response, start_timestamp, log_failures)
        return response.json()

    def is_group_id_unique(self, group_id):
        """
        Checks if the provided group_id is unique in Marathon
        """
        all_groups = self.get_group_ids(group_id)

        if len(all_groups) == 1:
            if all_groups[0] == group_id:
                return True

        return False

    def _wait_for_deployment_complete(self, deployment_response, start_timestamp, log_failures=True):
        """
        Waits for deployment to Marathon to complete. We start an instance of
        DeploymentMonitor that streams events from Marathon endpoint and monitors when
        apps fail or succeed to deploy. Monitor also logs any app status changes.
        """
        # Get the deploymentId, so we can uniquely identify deployment
        # we want to monitor
        deployment_json = deployment_response.json()
        if 'deploymentId' in deployment_json:
            deployment_id = deployment_json['deploymentId']
        elif 'deployments' in deployment_json:
            deployment_id = deployment_json['deployments'][0]['id']
        else:
            raise Exception(
                'Could not find "deploymentId" in {}'.format(deployment_json))

        # Get the affected apps for the deployment that was started
        # or just return if deployment already completed.
        get_deployments_response = self.get_deployments().json()
        a_deployment = [dep for dep in get_deployments_response if dep['id'] == deployment_id]
        if len(a_deployment) > 0:
            app_ids = a_deployment[0]['affectedApps']
        else:
            # Nothing to do
            return

        deployment_completed = False
        timeout_exceeded = False
        processor_catchup = False # Did we already give processor an extra second to finish up or not?
        processor = DeploymentMonitor(self, app_ids, deployment_id, log_failures)
        processor.start()

        while not deployment_completed:
            if self._wait_time_exceeded(self.deployment_max_wait_time, start_timestamp):
                timeout_exceeded = True
                break
            get_deployments_response = self.get_deployments().json()
            a_deployment = [dep for dep in get_deployments_response if dep['id'] == deployment_id]
            if len(a_deployment) == 0:
                if not processor_catchup:
                    logging.debug('Giving deployment monitor more time to catch-up on events')
                    for _ in range(0, 5):
                        if not processor.deployment_succeeded():
                            time.sleep(1)
                    # TODO:Check that the group was deployed correctly (instance count, healthcheck)
                    processor_catchup = True
                    continue
                else:
                    deployment_completed = True
                    break
            time.sleep(1)

        processor.stopped = True
        if timeout_exceeded:
            raise Exception('Timeout exceeded waiting for deployment to complete')

        if deployment_completed:
            logging.info('Deployment ended')

    def _wait_time_exceeded(self, max_wait, timestamp):
        """
        Checks if the wait time was exceeded.
        """
        return time.time() - timestamp > max_wait
