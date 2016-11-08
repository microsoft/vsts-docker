import logging
import pipes
import re

import healthcheck
import portmappings


class Parser(object):
    def __init__(self, group_name, service_name, service_info):
        self.service_name = service_name
        self.service_info = service_info
        self.group_name = group_name

        self.portmappings_helper = portmappings.PortMappings()
        self.app_json = {}

    def get_app_json(self):
        """
        Gets the app.json for the service in docker-compose
        """
        self.app_json = self._get_empty_app_json()
        self.app_json['id'] = '{}/{}'.format(self.group_name, self.service_name)

        for key in self.service_info:
            # We look for the method named _parse_{key} (for example: _parse_ports)
            # and execute it to parse that key.
            # If we decide to support more stuff from docker-compose, we
            # can simply add a method named _parse_NEWKEY and implement how the
            # key translates to Marathon JSON.
            method_name = '_parse_{}'.format(key)
            if hasattr(self, method_name):
                logging.info('Parsing key "%s"', key)
                method_to_call = getattr(self, method_name)
                method_to_call(key)
        return self.app_json

    def _parse_command(self, key):
        """
        Parses the 'command' key
        """
        if key in self.service_info:
            self.app_json['cmd'] = self._to_quoted_string(self.service_info[key])

    def _parse_cpu_shares(self, key):
        """
        Parses the 'cpu_shares' key
        """
        if key in self.service_info:
            self.app_json['cpus'] = float(self.service_info[key]) / 1024

    def _parse_entrypoint(self, key):
        """
        Parses the 'entrypoint' key
        """
        if key in self.service_info:
            entrypoint = self._to_quoted_string(self.service_info[key])
            self._append_parameters_key_value('entrypoint', entrypoint)

    def _parse_environment(self, key):
        """
        Parses the 'environment' key
        """
        if key in self.service_info:
            if not 'env' in self.app_json:
                self.app_json['env'] = {}
            for env_pair in self.service_info[key]:
                if isinstance(self.service_info[key], list):
                    if '=' in env_pair:
                        env_split = env_pair.split('=')
                        env_var_name = env_split[0]
                        env_var_value = env_split[1]
                        self.app_json['env'][env_var_name] = env_var_value
                    else:
                        # If environment var does not have a value set
                        self.app_json['env'][env_pair] = ''
                else:
                    value = self.service_info[key][env_pair]
                    if value is None:
                        self.app_json['env'][env_pair] = ''
                    else:
                        self.app_json['env'][env_pair] = str(value)

    def _parse_extra_hosts(self, key):
        """
        Parses the 'extra_hosts' key
        """
        if key in self.service_info:
            for host in self.service_info[key]:
                self._append_parameters_key_value('add-host', host)

    def _parse_labels(self, key):
        """
        Parses the 'labels' key
        """
        if key in self.service_info:

            # Add healthchecks (if any healthcheck labels are set)
            healthcheck_helper = healthcheck.HealthCheck(self.service_info[key])
            healthcheck_json = healthcheck_helper.get_health_check_config()
            if not healthcheck_json is None:
                self.app_json['healthChecks'] = healthcheck_json

            for label in self.service_info[key]:
                if not label.lower().startswith('com.microsoft.acs.dcos'):
                    if not 'labels' in self.app_json:
                        self.app_json['labels'] = {}
                    if isinstance(self.service_info[key], dict):
                        self.app_json['labels'][label] = str(self.service_info[key][label])
                    else:
                        if '=' in label:
                            label_split = label.split('=')
                            label_name = label_split[0]
                            label_value = label_split[1]
                            self.app_json['labels'][label_name] = str(label_value)
                        else:
                            # label without a value
                            self.app_json['labels'][label] = ''

    def _parse_mem_limit(self, key):
        """
        Parses the 'mem_limit' key
        """
        if key in self.service_info:
            mem_str = str(self.service_info[key]).strip()
            # String could be provided without a unit (default is bytes)
            if not re.search('[a-zA-Z]$', mem_str):
                unit = 'B'
                value = float(mem_str)
            else:
                unit = mem_str[-1].upper()
                value = float(mem_str[:len(mem_str)-1])

            if unit == 'B':
                total_bytes = value
            elif unit == 'K':
                total_bytes = value * 1024
            elif unit == 'M':
                total_bytes = value * 1024 * 1024
            elif unit == 'G':
                total_bytes = value * 1024 * 1024 * 1024
            self.app_json['mem'] = float(total_bytes) / (1024*1024)

    def _parse_stop_signal(self, key):
        """
        Parses the 'stop_signal' key
        """
        if key in self.service_info:
            stop_signal = self.service_info[key]
            self._append_parameters_key_value('stop-signal', stop_signal)

    def _parse_privileged(self, key):
        """
        Parses the 'privileged' key
        """
        if key in self.service_info:
            if not 'container' in self.app_json:
                self.app_json['container'] = {'docker': {}}
            self.app_json['container']['docker']['privileged'] = self.service_info[key]

    def _parse_user(self, key):
        """
        Parses the 'user' key
        """
        if key in self.service_info:
            user = self.service_info[key]
            self.app_json['user'] = user

    def _parse_working_dir(self, key):
        """
        Parses the 'working_dir' key
        """
        if key in self.service_info:
            work_dir = self.service_info[key]
            self._append_parameters_key_value('working_dir', work_dir)

    def _parse_image(self, key):
        """
        Parses the 'image' key
        """
        if key in self.service_info:
            if not 'container' in self.app_json:
                self.app_json['container'] = {'docker': {}}
            self.app_json['container']['docker']['image'] = self.service_info[key]

    def _append_parameters_key_value(self, key, value):
        """
        Appends a key/value pair to docker parameters section
        """
        if not 'container' in self.app_json:
            self.app_json['container'] = {'docker': {'parameters': []}}
        self.app_json['container']['docker']['parameters'].append(
            {'key': key, 'value': value})

    def _get_empty_app_json(self):
        app_json = {
            'id': '',
            'cpus': 0.1,
            'mem': 256,
            'instances': 0,
            'container': {
                'docker': {
                    'network': 'BRIDGE',
                    'portMappings': [{
                        'containerPort': 0,
                        'hostPort': 0,
                        'protocol': 'tcp',
                        'labels': {
                        }
                    }],
                    "parameters": []
                }
            },
            'labels': {
            },
            'dependencies': [],
            'env': {}
        }
        return app_json

    def _to_quoted_string(self, args):
        """
        Converts arguments to a properly quoted string
        """
        cmd_string = ''

        if not args:
            return args

        if isinstance(args, list):
            for arg in args:
                cmd_string += pipes.quote(str(arg)) + ' '
        else:
            cmd_string = pipes.quote(args)
        return cmd_string.strip()
