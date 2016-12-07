import json
import logging
import os
import time

from dcos.mesos import Mesos


class Marathon(object):
    """
    Class used for working with Marathon API
    """
    # Max time to wait (in seconds) for deployments to complete
    deployment_max_wait_time = 5 * 60

    def __init__(self, acs_client):
        self.acs_client = acs_client
        self.mesos = Mesos(self.acs_client)

    def get_request(self, path, endpoint='marathon/v2'):
        """
        Makes an HTTP GET request
        """
        return self.acs_client.get_request('{}/{}'.format(endpoint, path))

    def delete_request(self, path, endpoint='marathon/v2'):
        """
        Makes an HTTP DELETE request
        """
        return self.acs_client.delete_request('{}/{}'.format(endpoint, path))

    def post_request(self, path, post_data, endpoint='marathon/v2'):
        """
        Makes an HTTP POST request
        """
        return self.acs_client.post_request('{}/{}'.format(endpoint, path),
                                            post_data=post_data)

    def put_request(self, path, put_data=None, endpoint='marathon/v2', **kwargs):
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

    def scale_group(self, group_id, scale_factor):
        """
        Scales the group for provided scale_factor
        """
        start_timestamp = time.time()
        response = self.put_request('groups/{}'.format(group_id), json={'scaleBy': scale_factor})
        self._wait_for_deployment_complete(response, start_timestamp)
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

    def _wait_for_deployment_complete(self, deployment_response, start_timestamp):
        """
        Waits for the deployment to complete.
        """
        sleep_time = 5
        other_deployment_in_progress = False
        timeout_exceeded = True
        task_failed = False
        deployment_json = deployment_response.json()

        if 'deploymentId' in deployment_json:
            deployment_id = deployment_json['deploymentId']
        elif 'deployments' in deployment_json:
            deployment_id = deployment_json['deployments'][0]['id']
        else:
            raise Exception(
                'Could not find "deploymentId" in {}'.format(deployment_json))

        service_states = {}
        get_deployments_response = self.get_deployments().json()

        while not self._wait_time_exceeded(self.deployment_max_wait_time, start_timestamp) \
         and not other_deployment_in_progress and not task_failed:
            if not get_deployments_response:
                timeout_exceeded = False
                break

            a_deployment = [dep for dep in get_deployments_response if dep['id'] == deployment_id]

            if len(a_deployment) == 0:
                logging.info('Another service is being deployed. Continuing ...')
                other_deployment_in_progress = True
                break

            a_deployment = a_deployment[0]

            for affected_app in a_deployment['affectedApps']:
                service_id = affected_app.strip('/').replace('/', '_')

                if not service_id in service_states:
                    service_states[service_id] = None

                current_task = self.mesos.get_latest_task(service_id)

                if not current_task:
                    time.sleep(sleep_time)
                    continue

                current_state = current_task.state
                if service_states[service_id] != current_state:
                    logging.info('Service "%s" is in state: "%s"',
                                 service_id, current_state)

                    if current_task.is_failed() or\
                        current_task.is_killed():
                        logging.error('Service "%s" failed with status "%s".',
                                      service_id, current_state)

                        # Write out app logs
                        stdout = self.mesos.get_task_log_file(
                            current_task, 'stdout')
                        stderr = self.mesos.get_task_log_file(
                            current_task, 'stderr')

                        logging.info('stdout:\n%s', stdout)
                        logging.info('stderr:\n%s', stderr)
                        task_failed = True
                        break

                    service_states[service_id] = current_task.get_state()

            time.sleep(sleep_time)
            get_deployments_response = self.get_deployments().json()

        if task_failed or timeout_exceeded:
            raise Exception('Deployment failed to complete')

        return

    def _wait_time_exceeded(self, max_wait, timestamp):
        """
        Checks if the wait time was exceeded.
        """
        return time.time() - timestamp > max_wait
