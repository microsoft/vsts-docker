class ClusterInfo(object):
    """
    Holds info about the ACS cluster
    """
    def __init__(self, host, port, username, password, private_key, api_endpoint, orchestrator):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.api_endpoint = api_endpoint
        self.orchestrator = orchestrator

    def get_api_endpoint_port(self):
        """
        Gets the API endpoint port based on the orchestrator type
        """
        if self.orchestrator.lower() == 'kubernetes':
            return 8080
        elif self.orchestrator.lower() == 'dcos':
            return 80
        else:
            raise ValueError('Invalid orchestrator type')
