
class MesosTask(object):
    """
    Class represents a Mesos task
    """
    def __init__(self, task, directory):
        if not 'id' in task:
            raise ValueError('Task is missing "id" ')
        if not 'slave_id' in task:
            raise ValueError('Task is missing "slave_id"')
        if not 'framework_id' in task:
            raise ValueError('Task is missing "framework_id"')
        if not 'state' in task:
            raise ValueError('Task is missing "state"')
        if not 'statuses' in task:
            raise ValueError('Task is missing "statuses"')

        self.task_id = task['id']
        self.slave_id = task['slave_id']
        self.framework_id = task['framework_id']
        self.directory = directory
        self.state = task['state']

        statuses = [ts for ts in task['statuses']]
        if len(statuses) == 0:
            timestamp = -1
        else:
            statuses.sort(key=lambda s: s['timestamp'], reverse=True)
            timestamp = statuses[0]['timestamp']
        self.timestamp = timestamp

    def get_sandbox_path(self, filename):
        """
        Gets the path to the sandbox
        """
        if not filename:
            raise ValueError('Filename is not set')

        url_template = '{}/files/read.json?path={}/{}&length=999999&offset=0'
        return url_template.format(
            self.slave_id, self.directory, filename)

    def is_failed(self):
        """
        Returns True if task failed, False otherwise
        """
        return self.state == 'TASK_FAILED'

    def is_killed(self):
        """
        Returns True if task is killed or being killed, false otherwise
        """
        return self.state == 'TASK_KILLED' or self.state == 'TASK_KILLING'
