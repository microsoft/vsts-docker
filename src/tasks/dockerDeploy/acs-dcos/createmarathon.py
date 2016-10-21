import argparse
import sys
import traceback

import dockercomposeparser


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
                        help='[required] Registry host (e.g. myreg.azurecr.io)')
    parser.add_argument('--registry-username',
                        help='[required] Registry user name')
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
    if args.registry_host is None:
        arg_parser.error('argument --registry-host/-r is required')
    if args.registry_username is None:
        arg_parser.error('argument --registry-username/-u is required')
    if args.registry_password is None:
        arg_parser.error('argument --registry-password/-p is required')
    return args

if __name__ == '__main__':
    arguments = process_arguments()
    try:
        compose_parser = dockercomposeparser.DockerComposeParser(
            arguments.compose_file, arguments.dcos_master_url, arguments.acs_host,
            arguments.acs_port, arguments.acs_username, arguments.acs_password,
            arguments.acs_private_key, arguments.group_name, arguments.group_qualifier,
            arguments.group_version, arguments.registry_host, arguments.registry_username,
            arguments.registry_password, arguments.minimum_health_capacity)

        compose_parser.deploy()
        sys.exit(0)
    except Exception as e:
        var = traceback.format_exc()
        print var
        sys.exit(1)
