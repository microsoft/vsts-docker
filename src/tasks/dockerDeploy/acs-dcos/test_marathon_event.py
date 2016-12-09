import unittest

from marathon_deployments import MarathonEvent


class MarathonEventTest(unittest.TestCase):
    def test_not_none(self):
        m = MarathonEvent({})
        self.assertIsNotNone(m)

    def test_get_event_type(self):
        m = MarathonEvent({'eventType': 'SomeEvent'})
        self.assertEqual(m._get_event_type(), 'SomeEvent') 

    def test_get_event_type_unknown(self):
        m = MarathonEvent({'blah': 'SomeEvent'})
        self.assertEqual(m._get_event_type(), 'UNKNOWN') 

    def test_get_app_id(self):
        m = MarathonEvent({'appId': 'appid'})
        self.assertEqual(m.app_id(), 'appid') 

    def test_get_app_id_missing(self):
        m = MarathonEvent({'blah': 'appid'})
        self.assertRaises(KeyError, m.app_id)

    def test_get_task_id(self):
        m = MarathonEvent({'taskId': 'taskid'})
        self.assertEqual(m.task_id(), 'taskid') 

    def test_get_task_id_missing(self):
        m = MarathonEvent({'blah': 'blah'})
        self.assertRaises(KeyError, m.task_id)

    def test_get_slave_id(self):
        m = MarathonEvent({'slaveId': 'slaveid'})
        self.assertEqual(m.slave_id(), 'slaveid') 

    def test_get_slave_id_missing(self):
        m = MarathonEvent({'blah': 'blah'})
        self.assertRaises(KeyError, m.slave_id)

    def test_get_task_status(self):
        m = MarathonEvent({'taskStatus': 'status'})
        self.assertEqual(m._get_task_status(), 'status') 

    def test_get_task_status_missing(self):
        m = MarathonEvent({'blah': 'blah'})
        self.assertRaises(KeyError, m._get_task_status)

    def test_is_status_update_true(self):
        m = MarathonEvent({'eventType': 'status_update_event'})
        self.assertTrue(m.is_status_update())

    def test_is_status_update_false(self):
        m = MarathonEvent({'eventType': 'BLAH'})
        self.assertFalse(m.is_status_update())

    def test_is_deployment_succeeded_true(self):
        m = MarathonEvent({'eventType': 'deployment_success'})
        self.assertTrue(m.is_deployment_succeeded())

    def test_is_deployment_succeeded_false(self):
        m = MarathonEvent({'eventType': 'BLAH'})
        self.assertFalse(m.is_deployment_succeeded())

    def test_is_task_failed_true(self):
        m = MarathonEvent({'taskStatus': 'TASK_FAILED'})
        self.assertTrue(m.is_task_failed())

    def test_is_task_failed_false(self):
        m = MarathonEvent({'taskStatus': 'BLAH'})
        self.assertFalse(m.is_task_failed())

    def test_is_task_staging_true(self):
        m = MarathonEvent({'taskStatus': 'TASK_STAGING'})
        self.assertTrue(m.is_task_staging())

    def test_is_task_staging_false(self):
        m = MarathonEvent({'taskStatus': 'BLAH'})
        self.assertFalse(m.is_task_staging())

    def test_is_task_killed_true(self):
        m = MarathonEvent({'taskStatus': 'TASK_KILLED'})
        self.assertTrue(m.is_task_killed())

    def test_is_task_killed_false(self):
        m = MarathonEvent({'taskStatus': 'BLAH'})
        self.assertFalse(m.is_task_killed())

    def test_is_task_running_true(self):
        m = MarathonEvent({'taskStatus': 'TASK_RUNNING'})
        self.assertTrue(m.is_task_running())

    def test_is_task_running_false(self):
        m = MarathonEvent({'taskStatus': 'BLAH'})
        self.assertFalse(m.is_task_running())
