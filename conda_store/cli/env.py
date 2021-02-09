import sys
import yaml
from conda_store import client


def initialize_env_cli(subparser):
    parser = subparser.add_parser('env', help='manage conda environments')
    parser.add_argument('action', choices=['create', 'list', 'list-packages', 'get-sha'], help='action to take on conda environments')
    parser.add_argument('-f', '--filename', help='conda environment filename to use')
    parser.add_argument('-n', '--name', help='conda environment name specification')
    parser.add_argument('--build-id', help='build_id of a conda_store environment')
    parser.add_argument('--sha', help='sha256 of a conda_store environment')
    parser.set_defaults(func=handle_environment)


def _print_environments(data):
    print('{:10}{:32}{:32}'.format('BUILD', 'NAME', 'SHA256'))
    print("="*74)
    for row in data:
        name = row['name']
        build_id = row['build_id']
        sha256 = row.get('specification', {}).get('sha256')
        print(f'{build_id:<10}{name:32}{sha256[:32]:32}')


def _create_from_yaml(filename):
    with open(filename) as f:
        data = yaml.safe_load(f)
    client.post_specification(data)


def _print_environment_packages(data):
    print('{:32}{:16}{:48}{:32}'.format('NAME', 'VERSION', 'LICENSE', 'SHA256'))
    print("="*128)
    pkgs = data['specification']['builds'][0]['packages']
    for pkg in pkgs:
        name = pkg['name']
        version = pkg['version']
        license = pkg['license']
        sha = pkg['sha256']
        print(f'{name:32}{version:16}{license:48}{sha:32}')


def handle_environment(args):

    if args.action == 'list':
        _print_environments(client.get_environments())

    if args.action == 'create':
        if not args.filename:
            print("Please supply an environment yaml file using '-f'")
            sys.exit(0)
        _create_from_yaml(args.filename)

    if args.action == 'list-packages':
        if not args.name:
            print("Please supply an environment name using flag '-n'")
            sys.exit(0)
        _print_environment_packages(client.get_environment_packages(name=args.name))
