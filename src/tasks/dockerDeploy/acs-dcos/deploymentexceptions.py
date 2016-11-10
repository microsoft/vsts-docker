
class DeploymentException(Exception):
    """
    Exception that occurs during deployment
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class DeploymentExistsException(DeploymentException):
    """
    Exception that occurs if deployment already exists
    If this is thrown we should not call cleanup
    """
    def __init__(self, *args, **kwargs):
        DeploymentException.__init__(self, *args, **kwargs)

class DeploymentNotUniqueException(DeploymentException):
    """
    Exception that occurs another deployment with the same
    ID was deployed while deploying our services
    """
    def __init__(self, *args, **kwargs):
        DeploymentException.__init__(self, *args, **kwargs)

class NoExposedPortsException(DeploymentException):
    """
    Exception that occurs if no ports are exposed in the compose file
    """
    def __init__(self, *args, **kwargs):
        DeploymentException.__init__(self, *args, **kwargs)

class MissingComposeFileException(Exception):
    """
    Exception that occurs if docker-compose file is missing
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)