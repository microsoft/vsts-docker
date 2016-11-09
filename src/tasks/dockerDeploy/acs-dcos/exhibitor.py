
class Exhibitor(object):
    """
    Functionality for interacting with exhbitior
    """
    APP_ID = '/exhibitor-data'
    HOST_NAME = 'exhibitor-data.marathon.l4lb.thisdcos.directory'
    JSON_FILE = 'conf/exhibitor-data.json'

    def __init__(self, marathon_helper):
        self.marathon_helper = marathon_helper

    def upload(self, hex_string, endpoint):
        """
        Uploads a hexified string to provided exhibitor endpoint
        and returns the full URL to it
        """
        self.marathon_helper.put_request(
            endpoint,
            put_data=hex_string,
            endpoint='/exhibitor/exhibitor/v1/explorer/znode')

        return 'http://{}/{}'.format(
            Exhibitor.HOST_NAME, endpoint)
