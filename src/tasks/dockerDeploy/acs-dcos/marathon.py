import json
import time

import acsclient


class Marathon(object):
    """
    Class used for working with Marathon API
    """
    # Max time to wait (in seconds) for deployments to complete
    deployment_max_wait_time = 5 * 60

    def __init__(self, acs_info):
        self.acs_client = acsclient.ACSClient(acs_info)

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
            raise ValueError('Missing group_id')

        if force is None:
            force = True

        response = self.delete_request('groups/{}?force={}'.format(group_id, force))
        return response

    def get_deployments(self):
        """
        Gets all deployments from Marathon
        """
        return self.get_request('deployments')

    def get_app(self, app_id):
        """
        Gets the definition of the app (json), running in marathon.
        """
        if not app_id:
            raise ValueError('Missing app_id')
        return self.get_request('apps/{}'.format(app_id))

    def deploy_app(self, app_json):
        """
        Deploys an app to marathon
        """
        if not app_json:
            raise ValueError('Missing app json')

        start_timestamp = time.time()
        response = self.post_request('apps', post_data=app_json)

        if response.status_code >= 400:
            raise Exception('Something went wrong: {}'.format(response.text))

        response_json = response.json()

        if 'deployments' not in response_json:
            raise Exception('Something went wrong. Missing deployments: {}'.format(response_json))
        deployment_id = response_json['deployments'][0]['id']
        self._wait_for_deployment_complete(deployment_id, start_timestamp)

    def update_group(self, marathon_json):
        """
        Updates an existing marathon group
        """
        return self.__deploy_group(marathon_json, 'PUT')

    def deploy_group(self, marathon_json):
        """
        Deploys a new marathon group
        """
        return self.__deploy_group(marathon_json, 'POST')

    def __deploy_group(self, marathon_json, method):
        """
        Creates and starts a new application group defined in marathon_json
        """
        if not marathon_json:
            raise ValueError('Missing marathon json')

        start_timestamp = time.time()
        if method == 'POST':
            response = self.post_request('groups', json.dumps(marathon_json))
        elif method == 'PUT':
            response = self.put_request('groups', put_data=json.dumps(marathon_json))
        else:
            raise ValueError('Invalid method "{}"'.format(method))

        if response.status_code >= 400:
            raise Exception('Something went wrong: {}'.format(response.text))

        response_json = response.json()

        if 'deploymentId' not in response_json:
            raise Exception('Something went wrong. Missing deploymentId: {}'.format(response_json))
        deployment_id = response_json['deploymentId']
        self._wait_for_deployment_complete(deployment_id, start_timestamp)
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
        if response.status_code >= 400:
            raise Exception('Something went wrong: {}'.format(response.text))

        deployment_id = response.json().get('deploymentId')
        self._wait_for_deployment_complete(deployment_id, start_timestamp)
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

    def _wait_for_deployment_complete(self, deployment_id, start_timestamp):
        """
        Waits for the deployment to complete.
        """
        other_deployment_in_progress = False
        while not self._wait_time_exceeded(self.deployment_max_wait_time, start_timestamp) \
         and not other_deployment_in_progress:
            response = self.get_deployments().json()
            if response:
                for a_deployment in response:
                    if deployment_id in a_deployment['id']:
                        print 'Waiting for deployment "{}" to complete ...'.format(deployment_id)
                        time.sleep(5)
                    else:
                        print 'Another service is being deployed. Ignoring ...'
                        other_deployment_in_progress = True
                        timeout_exceeded = False
                        break
            else:
                timeout_exceeded = False
                break

        if timeout_exceeded:
            raise Exception('Timeout exceeded waiting for deployment to complete')
        return

    def _wait_time_exceeded(self, max_wait, timestamp):
        """
        Checks if the wait time was exceeded.
        """
        return time.time() - timestamp > max_wait
