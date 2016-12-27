import logging
import os
import socket
import subprocess
import time
from StringIO import StringIO

import paramiko
import requests
from sshtunnel import SSHTunnelForwarder


class ACSClient(object):
    """
    Class for connecting to the ACS cluster and making requests
    """
    current_tunnel = ()
    # Max wait time (seconds) for tunnel to be established
    max_wait_time = 5 * 60

    def __init__(self, cluster_info):
        self.cluster_info = cluster_info
        self.tunnel_server = None
        self.is_direct = False
        self.is_running = False

        # If master_url is provided, we have a direct connection
        if self.cluster_info.api_endpoint:
            logging.debug('Using Direct connection')
            self.is_direct = True
        else:
            logging.debug('Using SSH connection')

    def shutdown(self):
        """
        Stops the tunnel if its started
        """
        if self.current_tunnel and self.is_running:
            logging.debug('Stopping SSH tunnel')
            self.current_tunnel[0].stop()
            self.is_running = False

    def _wait_for_tunnel(self, start_time, url):
        """
        Waits until the SSH tunnel is available and
        we can start sending requests through it
        """
        succeeded = False
        while not time.time() - start_time > self.max_wait_time:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    succeeded = True
                    self.is_running = True
                    break
            except:
                time.sleep(5)

        if not succeeded:
            raise Exception(
                'Could not establish connection to "{}".'.format(
                    self.cluster_info.host))

    def _get_private_key(self):
        """
        Creates an RSAKey instance from provided private key string
        and password
        """
        if not self.cluster_info.private_key:
            raise Exception('Private key was not provided')
        private_key_file = StringIO()
        private_key_file.write(self.cluster_info.private_key)
        private_key_file.seek(0)
        return paramiko.RSAKey.from_private_key(private_key_file, self.cluster_info.password)

    def _setup_tunnel_server(self):
        """
        Gets the local port to access the tunnel
        """
        if not self.current_tunnel:
            logging.debug('Create a new SSH tunnel')
            local_port = self.get_available_local_port()
            log = logging.getLogger()
            previous_log_level = log.level
            log.setLevel(logging.INFO)

            forwarder = SSHTunnelForwarder(
                ssh_address_or_host=(self.cluster_info.host, int(self.cluster_info.port)),
                ssh_username=self.cluster_info.username,
                ssh_pkey=self._get_private_key(),
                remote_bind_address=('localhost', self.cluster_info.get_api_endpoint_port()),
                local_bind_address=('0.0.0.0', int(local_port)),
                logger=log)
            forwarder.start()

            start_time = time.time()
            url = 'http://127.0.0.1:{}/'.format(str(local_port))
            self._wait_for_tunnel(start_time, url)

            self.current_tunnel = (forwarder, int(local_port))
            log.setLevel(previous_log_level)

        return self.current_tunnel[1]

    def create_request_url(self, path):
        """
        Creates the request URL from provided path. Depending on which
        connection type was picked, it will create an SSH tunnel
        """
        if self.is_direct:
            url = '{}:{}/{}'.format(
                self.cluster_info.api_endpoint, self.cluster_info.get_api_endpoint_port(), path)
        else:
            local_port = self._setup_tunnel_server()
            url = 'http://127.0.0.1:{}/{}'.format(str(local_port), path)
        return url

    def make_request(self, path, method, data=None, port=None, **kwargs):
        """
        Makes an HTTP request with specified method
        """
        url = self.create_request_url(path)
        logging.debug('%s: %s (DATA=%s)', method, url, data)

        if not hasattr(requests, method):
            raise Exception('Invalid method {}'.format(method))

        method_to_call = getattr(requests, method)
        headers = {'content-type': 'application/json'}

        if not data:
            response = method_to_call(
                url, headers=headers, **kwargs)
        else:
            response = method_to_call(
                url, data, headers=headers, **kwargs)

        if response.status_code > 400:
            raise Exception('Call to "%s" failed with: %s', url, response.text)
        return response

    def get_request(self, path):
        """
        Makes a GET request to an endpoint (localhost:80 on the cluster)
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        return self.make_request(path, 'get')

    def delete_request(self, path):
        """
        Makes a DELETE request to an endpoint (localhost:80 on the cluster)
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        return self.make_request(path, 'delete')

    def post_request(self, path, post_data):
        """
        Makes a POST request to an endpoint (localhost:80 on the cluster)
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        return self.make_request(path, 'post', data=post_data)

    def put_request(self, path, put_data=None, **kwargs):
        """
        Makes a POST request to Marathon endpoint (localhost:80 on the cluster)
        :param path: Path part of the URL to make the request to
        :type path: String
        """
        return self.make_request(path, 'put', data=put_data, **kwargs)

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
