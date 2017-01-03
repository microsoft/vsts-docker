import json
import logging
import re
import threading

import sseclient


class MarathonEvent(object):
    """
    Represens a single event from Marathon
    """
    def __init__(self, data):
        self.data = data

    def _get_event_type(self):
        """
        Gets the event type
        """
        if not 'eventType' in self.data:
            return 'UNKNOWN'
        return self.data['eventType']

    def app_id(self):
        """
        Gets the appId
        """
        return self.data['appId']

    def task_id(self):
        """
        Gets the taskId
        """
        return self.data['taskId']

    def slave_id(self):
        """
        Gets the slaveId
        """
        return self.data['slaveId']

    def _get_task_status(self):
        """
        Gets the task status
        """
        return self.data['taskStatus']

    def is_status_update(self):
        """
        True if event represents a status update
        """
        return self._get_event_type() == 'status_update_event'

    def is_group_change_success(self):
        """
        True if event represents a group change success
        """
        return self._get_event_type() == 'group_change_success'

    def is_app_terminated(self):
        """
        True if event represents an app terminated event
        """
        return self._get_event_type() == 'app_terminated_event'

    def is_task_failed(self):
        """
        True if task is failed, false otherwise
        """
        return self._get_task_status() == 'TASK_FAILED'

    def is_task_staging(self):
        """
        True if task is staging, false otherwise
        """
        return self._get_task_status() == 'TASK_STAGING'

    def is_task_running(self):
        """
        True if task is running, false otherwise
        """
        return self._get_task_status() == 'TASK_RUNNING'

    def is_task_killed(self):
        """
        True if task is killed, false otherwise
        """
        return self._get_task_status() == 'TASK_KILLED'

    def is_task_killing(self):
        """
        True if task is being killed, false otherwise
        """
        return self._get_task_status() == 'TASK_KILLING'

    def is_task_finished(self):
        """
        True if task is finished, false otherwise
        """
        return self._get_task_status() == 'TASK_FINISHED'

    def is_deployment_succeeded(self):
        """
        True if event represents a successful deployment
        """
        return self._get_event_type() == 'deployment_success'

    def is_deployment_failed(self):
        """
        True if event represents a failed deployment
        """
        return self._get_event_type() == 'deployment_failed'

    def status(self):
        """
        Gets the event status
        """
        event_status = ""
        if self.is_task_running():
            event_status = 'Service "{}" task is running'.format(self.app_id())
        elif self.is_task_staging():
            event_status = 'Service "{}" task is being staged'.format(self.app_id())
        elif self.is_task_failed():
            event_status = 'Service "{}" task has failed: {}'.format(
                self.app_id(), self.data['message'])
        elif self.is_task_killed():
            event_status = 'Service "{}" task was killed: {}'.format(
                self.app_id(), self.data['message'])
        elif self.is_task_killing():
            if self.data['message'].strip() == '':
                event_status = 'Service "{}" task is being killed.'.format(self.app_id())
            else:
                event_status = 'Service "{}" task is being killed: {}'.format(
                    self.app_id(), self.data['message'])
        elif self.is_task_finished():
            if self.data['message'].strip() == '':
                event_status = 'Service "{}" task is finished.'.format(self.app_id())
            else:
                event_status = 'Service "{}" task is finished: {}'.format(
                    self.app_id(), self.data['message'])
        elif self.is_app_terminated():
            event_status = 'Service "{}" was terminated.'.format(self.app_id())

        return event_status

class DeploymentMonitor(object):
    """
    Monitors deployment of apps to Marathon using their
    app IDs
    """
    def __init__(self, marathon, app_ids, deployment_id, log_failures=True):
        self._log_failures = log_failures
        self._marathon = marathon
        self._deployment_succeeded = False
        self._app_ids = app_ids
        self._deployment_id = deployment_id
        self.stopped = False
        self._thread = threading.Thread(
            target=DeploymentMonitor._process_events, args=(self,))

    def start(self):
        """
        Starts the deployment monitor
        """
        self._thread.daemon = True
        self._thread.start()

    def deployment_succeeded(self):
        """
        True if deployment succeeded, false otherwise
        """
        return self._deployment_succeeded

    def _process_events(self):
        """
        Reads the event stream from Marathon and handles events
        """
        events = self._get_event_stream()
        for event in events:
            try:
                self._log_event(event)
            except:
                # Ignore any exceptions
                pass

    def _log_event(self, event):
        """
        Logs events from Marathon
        """
        if event.is_status_update() or event.is_app_terminated():
            if event.app_id() in self._app_ids:
                logging.info(event.status())
                if (event.is_task_failed() or event.is_task_killed()) and self._log_failures:
                    self._log_stderr(event)
        elif event.is_deployment_succeeded():
            if self._deployment_id == event.data['id']:
                self._deployment_succeeded = True

    def _log_stderr(self, event):
        """
        Logs the stderr of the failed event
        """
        failed_task = self._marathon.mesos.get_task(
            event.task_id(), event.slave_id())
        stderr = self._marathon.mesos.get_task_log_file(failed_task, 'stderr')
        logging.error(stderr)

    def _get_event_stream(self):
        """
        Gets the event stream by making a GET request to
        Marathon /events endpoint
        """
        events_url = self._marathon.get_url('service/marathon/v2/events')
        messages = sseclient.SSEClient(events_url)
        for msg in messages:
            if self.stopped:
                break
            try:
                json_data = json.loads(msg.data)
            except ValueError:
                logging.debug('Failed to parse event: %s', msg.data)
                continue
            event = MarathonEvent(json_data)
            yield event
