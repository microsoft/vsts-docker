import socket
import requests
from sshtunnel import SSHTunnelForwarder

class ACSClient(object):
    """
    Class for connecting to the ACS cluster and making requests
    """
    def __init__(self, acs_info):
        self.acs_info = acs_info
        self.tunnel_server = None
        self.is_direct = False

        # If host is not provided, we have a direct connection
        if not self.acs_info.host:
            self.is_direct = True

    def __get_tunnel_server(self):
        """
        Gets the SSHTunnelForwarder instance and local_port
        """
        if self.is_direct:
            return None, 80

        local_port = self.get_available_local_port()
        # TODO (peterj, 10/20/2016): Need to provide private key/passphrase here
        return SSHTunnelForwarder(
            (self.acs_info.host, self.acs_info.port),
            ssh_username=self.acs_info.username,
            remote_bind_address=('localhost', 8080),
            local_bind_address=('0.0.0.0', local_port)), local_port

    def __get_request_url(self, path, local_port=80):
        if self.is_direct:
            return 'http://leader.mesos/{}'.format(path)

        return 'http://localhost:{}/{}'.format(str(local_port), path)

    def get_request(self, path):
        """
        Makes a GET request to Marathon endpoint (localhost:8080 on the cluster)
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        server, local_port = self.__get_tunnel_server()

        if server:
            server.start()

        url = self.__get_request_url(path, local_port)
        response = requests.get(url)

        if server:
            server.stop()
        return response

    def delete_request(self, path):
        """
        Makes a DELETE request to Marathon endpoint (localhost:8080 on the cluster)
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        server, local_port = self.__get_tunnel_server()
        if server:
            server.start()

        url = self.__get_request_url(path, local_port)
        response = requests.delete(url)

        if server:
            server.stop()
        return response

    def post_request(self, path, post_data):
        """
        Makes a POST request to Marathon endpoint (localhost:8080 on the cluster)
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        server, local_port = self.__get_tunnel_server()

        if server:
            server.start()
        url = self.__get_request_url(path, local_port)
        response = requests.post(url, data=post_data)

        if server:
            server.stop()
        return response

    def put_request(self, path, put_data=None, **kwargs):
        """
        Makes a POST request to Marathon endpoint (localhost:8080 on the cluster)
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        server, local_port = self.__get_tunnel_server()

        if server:
            server.start()
        url = self.__get_request_url(path, local_port)
        response = requests.put(url, data=put_data, **kwargs)
        if server:
            server.stop()
        return response

    def get_available_local_port(self):
        """
        Gets a random, available local port
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        sock.listen(1)
        port = sock.getsockname()[1]
        sock.close()
        return port
