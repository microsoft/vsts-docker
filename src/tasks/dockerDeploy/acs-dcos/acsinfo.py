class AcsInfo(object):
    """
    Holds info about the ACS cluster
    """
    def __init__(self, host, port, username, password, private_key, master_url):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.master_url = master_url
