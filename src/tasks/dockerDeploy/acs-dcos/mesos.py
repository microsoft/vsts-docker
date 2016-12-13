from mesos_task import MesosTask

class Mesos(object):
    def __init__(self, acs_client):
        self.acs_client = acs_client

    def _get_request(self, endpoint, path):
        """
        Makes a GET request to ACS
        """
        return self.acs_client.make_request('{}/{}'.format(endpoint, path), 'get', port=80)

    def get_task_log_file(self, task, filename):
        """
        Gets the contents of a log file from the tasks sandbox
        """
        url_path = task.get_sandbox_download_path(filename)
        try:
            log_file_response = self._get_request('slave', url_path)
        except:
            return '<empty>'

        return log_file_response.content

    def _get_slave_ids(self):
        """
        Gets all slave IDs in the cluster
        """
        # GET /mesos/slaves/state.json
        response = self._get_request('mesos/slaves', 'state.json')
        response.raise_for_status()

        all_slaves = response.json()
        return [slave['id'] for slave in all_slaves['slaves']]

    def _get_slave_state(self, slave_id):
        """
        Gets the state.json for specified slave
        """
        slave_state_response = self._get_request(
            'slave', '{}/state.json'.format(slave_id))
        slave_state_response.raise_for_status()

        slave_state_json = slave_state_response.json()
        return slave_state_json

    def get_task(self, task_id, slave_id=None):
        """
        Go through all frameworks and executors and get all tasks that
        start with the service_id. Returns the latest task with information
        needed to get the files from the sandbox
        """
        framework_name = 'marathon'
        slave_ids = [slave_id]
        if not slave_id:
            slave_ids = self._get_slave_ids()

        found_tasks = []

        for slave_id in slave_ids:
            slave_state_json = self._get_slave_state(slave_id)

            # Get all 'marathon' frameworks
            marathon_frameworks = []
            marathon_frameworks.extend(
                [f for f in slave_state_json['frameworks'] if f['name'] == framework_name])
            marathon_frameworks.extend(
                [f for f in slave_state_json['completed_frameworks'] if f['name'] == framework_name])

            # Get all executors and completed executors where 'id' of the task
            # starts with the service_id
            executors = []
            for framework in marathon_frameworks:
                executors.extend(
                    [e for e in framework['executors'] if e['id'] == task_id])
                executors.extend(
                    [e for e in framework['completed_executors'] if e['id'] == task_id])

            for executor in executors:
                for task in executor['tasks']:
                    found_tasks.append(MesosTask(task, executor['directory']))

                for task in executor['completed_tasks']:
                    found_tasks.append(MesosTask(task, executor['directory']))

        # Sort the tasks, so the newest are on top
        found_tasks.sort(key=lambda task: task.timestamp, reverse=True)
        if len(found_tasks) == 0:
            return None

        return found_tasks[0]
