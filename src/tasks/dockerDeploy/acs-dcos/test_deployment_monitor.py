
import unittest
from mock import Mock, patch

from marathon_deployments import DeploymentMonitor, MarathonEvent


class DeploymentMonitorTests(unittest.TestCase):

    @patch('marathon.Marathon')
    def test_not_none(self, mock_marathon):
        m = DeploymentMonitor(mock_marathon, [], '')
        self.assertIsNotNone(m)

    @patch('marathon.Marathon')
    def test_start_called(self, mock_marathon):
        m = DeploymentMonitor(mock_marathon, [], '')
        m._thread = Mock()
        m.start()
        self.assertTrue(m._thread.start.called)
        self.assertTrue(m._thread.daemon)

    @patch('marathon.Marathon')
    def test_stop_called(self, mock_marathon):
        m = DeploymentMonitor(mock_marathon, [], '')
        m._thread = Mock()
        m.stop()
        self.assertTrue(m._stop_event.isSet())
        self.assertTrue(m._thread.stop.called)

    @patch('marathon.Marathon')
    def test_is_running(self, mock_marathon):
        m = DeploymentMonitor(mock_marathon, [], '')
        self.assertTrue(m.is_running())

    @patch('marathon.Marathon')
    def test_is_running_false(self, mock_marathon):
        m = DeploymentMonitor(mock_marathon, [], '')
        m._thread = Mock()
        m.stop()
        self.assertFalse(m.is_running())

    @patch('marathon.Marathon')
    def test_handle_event_status_update(self, mock_marathon):
        app_ids = ['app_1', 'app_2']
        m = DeploymentMonitor(mock_marathon, app_ids, '')
        m._thread = Mock()

        ev = MarathonEvent({'appId': 'app_1', 'taskStatus': 'some_status', 'eventType': 'status_update_event'})
        m._handle_event(ev)
        self.assertFalse(m._deployment_failed)
        self.assertFalse(m._deployment_succeeded)

    @patch('marathon.Marathon')
    def test_handle_event_status_update_failed(self, mock_marathon):
        app_ids = ['app_1', 'app_2']
        m = DeploymentMonitor(mock_marathon, app_ids, '')
        m._thread = Mock()

        ev = MarathonEvent({'appId': 'app_1', 'taskStatus': 'TASK_FAILED', 'eventType': 'status_update_event', 'message': 'somemessage'})
        m._handle_event(ev)
        self.assertTrue(m._deployment_failed)
        self.assertTrue(m._stop_event.isSet())
        self.assertTrue(m._thread.stop.called)
        self.assertIsNotNone(m._failed_event)
        self.assertEqual(ev, m._failed_event)
        self.assertFalse(m._deployment_succeeded)

    @patch('marathon.Marathon')
    def test_handle_event_deployment_succeeded(self, mock_marathon):
        app_ids = ['app_1', 'app_2']
        m = DeploymentMonitor(mock_marathon, app_ids, 'deployment_id')
        m._thread = Mock()

        ev = MarathonEvent({'id': 'deployment_id', 'appId': 'app_1', 'taskStatus': 'TASK_FAILED', 'eventType': 'deployment_success', 'message': 'somemessage'})
        m._handle_event(ev)
        self.assertFalse(m._deployment_failed)
        self.assertTrue(m._stop_event.isSet())
        self.assertTrue(m._thread.stop.called)
        self.assertIsNone(m._failed_event)
        self.assertTrue(m._deployment_succeeded)

    @patch('marathon.Marathon')
    def test_handle_event_app_not_in_list(self, mock_marathon):
        app_ids = ['app_X', 'app_Y']
        m = DeploymentMonitor(mock_marathon, app_ids, '')
        m._thread = Mock()

        ev = MarathonEvent({'appId': 'app_1', 'taskStatus': 'TASK_FAILED', 'eventType': 'status_update_event', 'message': 'somemessage'})
        m._handle_event(ev)
        self.assertFalse(m._deployment_failed)
        self.assertFalse(m._deployment_succeeded)
        self.assertFalse(m._stop_event.isSet())
        self.assertFalse(m._thread.stop.called)
        self.assertIsNone(m._failed_event)

    @patch('marathon.Marathon')
    def test_handle_event_deployment_not_in_list(self, mock_marathon):
        app_ids = ['app_X', 'app_Y']
        m = DeploymentMonitor(mock_marathon, app_ids, 'MY_DEPLOYMENT')
        m._thread = Mock()

        ev = MarathonEvent({'id': 'another_deply_id', 'appId': 'app_1', 'taskStatus': 'TASK_FAILED', 'eventType': 'deployment_success', 'message': 'somemessage'})
        m._handle_event(ev)
        self.assertFalse(m._deployment_failed)
        self.assertFalse(m._deployment_succeeded)
        self.assertFalse(m._stop_event.isSet())
        self.assertFalse(m._thread.stop.called)
        self.assertIsNone(m._failed_event)