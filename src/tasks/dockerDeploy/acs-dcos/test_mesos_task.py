import unittest
from mesos_task import MesosTask

class MesosTaskTest(unittest.TestCase):
    def test_not_none(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'mystate',
            'statuses': []
        }

        task = MesosTask(base_task, 'directory')
        self.assertIsNotNone(task)

    def test_missing_id(self):
        base_task = {
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'mystate',
            'statuses': []
        }
        self.assertRaises(ValueError, MesosTask, base_task, 'directory')

    def test_missing_slave_id(self):
        base_task = {
            'id': 'mytask_id',
            'framework_id': 'myframework_id',
            'state': 'mystate',
            'statuses': []
        }
        self.assertRaises(ValueError, MesosTask, base_task, 'directory')

    def test_missing_framework_id(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'state': 'mystate',
            'statuses': []
        }
        self.assertRaises(ValueError, MesosTask, base_task, 'directory')

    def test_missing_state(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'statuses': []
        }
        self.assertRaises(ValueError, MesosTask, base_task, 'directory')

    def test_missing_statuses(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'mystate'
        }
        self.assertRaises(ValueError, MesosTask, base_task, 'directory')

    def test_values_set(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'mystate',
            'statuses': []
        }

        task = MesosTask(base_task, 'directory')
        self.assertEqual(task.task_id, 'mytask_id')
        self.assertEqual(task.slave_id, 'myslave_id')
        self.assertEqual(task.framework_id, 'myframework_id')
        self.assertEqual(task.state, 'mystate')
        self.assertEqual(task.timestamp, -1)

    def test_sandbox_path(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'mystate',
            'statuses': []
        }
        task = MesosTask(base_task, 'directory')
        expected = 'myslave_id/files/read.json?path=directory/myfile&length=999999&offset=0'
        actual = task.get_sandbox_path('myfile')

        self.assertEqual(actual, expected)

    def test_sandbox_path_empty_filename(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'mystate',
            'statuses': []
        }
        task = MesosTask(base_task, 'directory')
        self.assertRaises(ValueError, task.get_sandbox_path, None)

    def test_is_failed(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'TASK_FAILED',
            'statuses': []
        }
        task = MesosTask(base_task, 'directory')
        self.assertTrue(task.is_failed())

    def test_is_failed_false(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'TASK_SOMETHING',
            'statuses': []
        }
        task = MesosTask(base_task, 'directory')
        self.assertFalse(task.is_failed())

    def test_is_killed(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'TASK_KILLED',
            'statuses': []
        }
        task = MesosTask(base_task, 'directory')
        self.assertTrue(task.is_killed())

    def test_is_killing(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'TASK_KILLING',
            'statuses': []
        }
        task = MesosTask(base_task, 'directory')
        self.assertTrue(task.is_killed())

    def test_is_killed_false(self):
        base_task = {
            'id': 'mytask_id',
            'slave_id': 'myslave_id',
            'framework_id': 'myframework_id',
            'state': 'TASK_FALSE',
            'statuses': []
        }
        task = MesosTask(base_task, 'directory')
        self.assertFalse(task.is_killed())