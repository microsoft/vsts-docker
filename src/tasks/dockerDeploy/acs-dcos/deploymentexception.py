
class DeploymentException(Exception):
    """
    Exception that occurs during deployment
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
