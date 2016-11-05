
import json

class HealthCheck(object):
    PATH_LABEL = 'com.microsoft.acs.dcos.marathon.healthcheck.path'
    PORT_INDEX_LABEL = 'com.microsoft.acs.dcos.marathon.healthcheck.portIndex'
    COMMAND_LABEL = 'com.microsoft.acs.dcos.marathon.healthcheck.command'
    HEALTH_CHECK_LABEL = 'com.microsoft.acs.dcos.marathon.healthcheck'
    HEALTH_CHECKS_LABEL = 'com.microsoft.acs.dcos.marathon.healthchecks'

    def __init__(self, labels):
        if labels is None:
            raise ValueError('Labels cannot be empty')
        self.labels = labels

    @staticmethod
    def get_default_health_check_config():
        """
        Gets the default (TCP) healthcheck config for Marathon
        """
        return {
            'portIndex': 0,
            'protocol': 'TCP',
            'gracePeriodSeconds': 300,
            'intervalSeconds': 5,
            'timeoutSeconds': 20,
            'maxConsecutiveFailures': 3
        }

    def _label_exists(self, name):
        """
        Checks if label exists and returns True/False
        """
        label_exists = False
        for label in self.labels:
            if '=' in label:
                if label.split('=')[0] == name:
                    label_exists = True
                    break
            else:
                if label == name:
                    label_exists = True
                    break

        return label_exists

    def _get_label_value(self, name):
        """
        Gets the label value or None if label doesn't exist
        """
        label_value = None
        for label in self.labels:
            if '=' in label:
                label_split = label.split('=')
                if label_split[0] == name:
                    label_value = label_split[1]
                    break
            else:
                if label == name:
                    label_value = self.labels[label]
                    break
        return label_value

    def _set_path_if_exists(self, healthcheck_json):
        """
        Sets the path in health check
        """
        if self._label_exists(self.PATH_LABEL):
            healthcheck_json['path'] = self._get_label_value(self.PATH_LABEL)
            healthcheck_json['protocol'] = 'HTTP'
        return healthcheck_json

    def _set_port_index_if_exists(self, healthcheck_json):
        """
        Sets the port index in health check
        """
        if self._label_exists(self.PORT_INDEX_LABEL):
            healthcheck_json['portIndex'] = self._get_label_value(self.PORT_INDEX_LABEL)
            healthcheck_json['protocol'] = 'HTTP'
        return healthcheck_json

    def _set_command_if_exists(self, healthcheck_json):
        """
        Sets the command in healthcheck
        """
        if self._label_exists(self.COMMAND_LABEL):
            healthcheck_json['command'] = {'value': self._get_label_value(self.COMMAND_LABEL)}
            healthcheck_json['protocol'] = 'COMMAND'
        return healthcheck_json

    def get_health_check_config(self):
        """
        Gets the health check config
        """
        healthcheck = None

        if self._label_exists(self.HEALTH_CHECK_LABEL) or \
            self._label_exists(self.PATH_LABEL) or \
            self._label_exists(self.PORT_INDEX_LABEL):
            healthcheck = HealthCheck.get_default_health_check_config()
            healthcheck = self._set_path_if_exists(healthcheck)
            healthcheck = self._set_port_index_if_exists(healthcheck)
        elif self._label_exists(self.COMMAND_LABEL):
            healthcheck = HealthCheck.get_default_health_check_config()
            healthcheck = self._set_command_if_exists(healthcheck)
        elif self._label_exists(self.HEALTH_CHECKS_LABEL):
            healthcheck = json.loads(self._get_label_value(self.HEALTH_CHECKS_LABEL))
        if not healthcheck is None and not isinstance(healthcheck, list):
            healthcheck = [healthcheck]

        return healthcheck
