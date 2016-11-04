import argparse
import logging
import sys
import traceback

import dockercomposeparser

class VstsLogFormatter(logging.Formatter):
    error_format = logging.Formatter('##[error] (%(name)s): %(message)s')
    warning_format = logging.Formatter('##[warning] (%(name)s): %(message)s')
    debug_format = logging.Formatter('##[debug] (%(name)s): %(message)s')
    default_format = logging.Formatter('%(levelname)s (%(name)s): %(message)s')

    def format(self, record):
        if record.levelno == logging.ERROR:
            return self.error_format.format(record)
        elif record.levelno == logging.WARNING:
            return self.warning_format.format(record)
        elif record.levelno == logging.DEBUG:
            return self.debug_format.format(record)
        return self.default_format.format(record)

def get_arg_parser():
    """
    Sets up the argument parser
    """
    parser = argparse.ArgumentParser(
        description='Translate docker-compose.yml file to marathon.json file',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--compose-file',
                        help='[required] Docker-compose.yml file')
    parser.add_argument('--dcos-master-url',
                        help='DC/OS master URL')

    parser.add_argument('--group-name',
                        help='[required] Application group name')
    parser.add_argument('--group-qualifier',
                        help='[required] Application group qualifier')
    parser.add_argument('--group-version',
                        help='[required] Application group version')
    parser.add_argument('--minimum-health-capacity', type=int,
                        help='[required] Minimum health capacity')

    parser.add_argument('--registry-host',
                        help='[required] Registry host (e.g. myregistry.azurecr-test.io:1234)')
    parser.add_argument('--registry-username',
                        help='[required] Registry username')
    parser.add_argument('--registry-password',
                        help='[required] Registry password')

    parser.add_argument('--acs-host',
                        help='ACS host')
    parser.add_argument('--acs-port',
                        help='ACS username')
    parser.add_argument('--acs-username',
                        help='ACS username')
    parser.add_argument('--acs-password',
                        help='ACS password')
    parser.add_argument('--acs-private-key',
                        help='ACS private key')

    parser.add_argument('--verbose',
                        help='Turn on verbose logging',
                        action='store_true')
    return parser

def process_arguments():
    """
    Makes sure required arguments are provided
    """
    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    if args.compose_file is None:
        arg_parser.error('argument --compose-file is required')
    if args.group_name is None:
        arg_parser.error('argument --group-name is required')
    if args.group_qualifier is None:
        arg_parser.error('argument --group-qualifier is required')
    if args.group_version is None:
        arg_parser.error('argument --group-version is required')
    if args.minimum_health_capacity is None:
        arg_parser.error('argument --minimum-health-capacity is required')
    return args

def init_logger(verbose):
    """
    Initializes the logger and sets the custom formatter for VSTS
    """
    logging_level = logging.DEBUG if verbose else logging.INFO
    vsts_formatter = VstsLogFormatter()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(vsts_formatter)
    logging.root.name = 'ACS-Deploy'
    logging.root.setLevel(logging_level)
    logging.root.addHandler(stream_handler)

    # Don't show INFO log messages from requests library
    logging.getLogger("requests").setLevel(logging.WARNING)

if __name__ == '__main__':
    arguments = process_arguments()
    init_logger(arguments.verbose)
    try:
        with dockercomposeparser.DockerComposeParser(
            arguments.compose_file, arguments.dcos_master_url, arguments.acs_host,
            arguments.acs_port, arguments.acs_username, arguments.acs_password,
            arguments.acs_private_key, arguments.group_name, arguments.group_qualifier,
            arguments.group_version, arguments.registry_host, arguments.registry_username,
            arguments.registry_password, arguments.minimum_health_capacity) as compose_parser:
            compose_parser.deploy()
        sys.exit(0)
    except Exception as e:
        var = traceback.format_exc()
        print var
        sys.exit(1)