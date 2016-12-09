import unittest
from mock import Mock, patch
from mesos import Mesos

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception('raise_for_status exception')
            else:
                pass

    if args[0].startswith('mesos/slaves/state.json'):
        return MockResponse({'slaves': [{'id': 'slave_1'}, {'id': 'slave_2'}]}, 200)
    elif args[0].startswith('slave/slave_1/state.json'):
        state = {
            'frameworks': [],
            'completed_frameworks': [{
                'id': 'framework_id',
                'name': 'marathon',
                'executors': [],
                'completed_executors': [{
                    'id': 'service_id',
                    'directory': 'completed_executor_1_directory',
                    'tasks':[],
                    'queued_tasks': [],
                    'completed_tasks': [{
                        'id': 'service_id',
                        'framework_id': 'framework_id',
                        'slave_id': 'slave_id',
                        'state': 'TASK_STATE',
                        'statuses': [{
                            'state': 'TASK_STATE_STATUS',
                            'timestamp': 1
                        }]
                    }]
                }]
            }]
        }
        return MockResponse(state, 200)
    elif args[0].startswith('slave/slave_2/state.json'):
        state = {
            'frameworks': [],
            'completed_frameworks': [{
                'id': 'framework_id_2',
                'name': 'marathon',
                'executors': [],
                'completed_executors': [{
                    'id': 'service_id',
                    'directory': 'completed_executor_2_directory',
                    'tasks':[],
                    'queued_tasks': [],
                    'completed_tasks': [{
                        'id': 'service_id',
                        'framework_id': 'framework_id_2',
                        'slave_id': 'slave_id',
                        'state': 'TASK_STATE',
                        'statuses': [{
                            'state': 'TASK_STATE_STATUS',
                            'timestamp': 2
                        }]
                    }]
                }]
            }]
        }
        return MockResponse(state, 200)
    elif args[0].startswith('save/404/state.json'):
        return MockResponse({}, 404)

    return MockResponse({}, 404)


class MesosTest(unittest.TestCase):
    @patch('acsclient.ACSClient')
    def test_not_none(self, mock_acs_client):
        m = Mesos(mock_acs_client)
        self.assertIsNotNone(m)

    @patch('acsclient.ACSClient')
    def test_get_request(self, mock_acs_client):
        m = Mesos(mock_acs_client)
        m._get_request('endpoint', 'path')
        mock_acs_client.get_request.assert_called_with('endpoint/path')

    @patch('acsclient.ACSClient')
    def test_get_slave_ids(self, mock_acs_client):
        mock_acs_client.get_request.side_effect = mocked_requests_get
        m = Mesos(mock_acs_client)
        actual = m._get_slave_ids()
        self.assertEqual(actual, ['slave_1', 'slave_2'])

    @patch('acsclient.ACSClient')
    def test_get_slave_state(self, mock_acs_client):
        mock_acs_client.get_request.side_effect = mocked_requests_get
        m = Mesos(mock_acs_client)
        actual = m._get_slave_state('slave_1')
        expected = state = {
            'frameworks': [],
            'completed_frameworks': [{
                'id': 'framework_id',
                'name': 'marathon',
                'executors': [],
                'completed_executors': [{
                    'id': 'service_id',
                    'directory': 'completed_executor_1_directory',
                    'tasks':[],
                    'queued_tasks': [],
                    'completed_tasks': [{
                        'id': 'service_id',
                        'framework_id': 'framework_id',
                        'slave_id': 'slave_id',
                        'state': 'TASK_STATE',
                        'statuses': [{
                            'state': 'TASK_STATE_STATUS',
                            'timestamp': 1
                        }]
                    }]
                }]
            }]
        }
        self.assertEqual(actual, expected)

    @patch('acsclient.ACSClient')
    def test_get_slave_state_404(self, mock_acs_client):
        mock_acs_client.get_request.side_effect = mocked_requests_get
        m = Mesos(mock_acs_client)
        self.assertRaises(Exception, m._get_slave_state, '404')

    @patch('acsclient.ACSClient')
    def test_get_latest_task(self, mock_acs_client):
        mock_acs_client.get_request.side_effect = mocked_requests_get
        m = Mesos(mock_acs_client)
        actual = m.get_task('service_id')
        self.assertEqual(actual.task_id, 'service_id')
        self.assertEqual(actual.slave_id, 'slave_id')
        self.assertEqual(actual.framework_id, 'framework_id_2')
        self.assertEqual(actual.state, 'TASK_STATE')
        self.assertEqual(actual.directory, 'completed_executor_2_directory')
        self.assertEqual(actual.timestamp, 2)
