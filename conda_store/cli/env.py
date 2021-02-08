import sys
import yaml
from conda_store import client


def initialize_env_cli(subparser):
    parser = subparser.add_parser('env', help='manage conda environments')
    parser.add_argument('action', choices=['create', 'list', 'list-packages'], help='action to take on conda environments')
    parser.add_argument('-f', '--filename', help='conda environment filename to use')
    parser.add_argument('-n', '--name', help='conda environment name specification')
    parser.set_defaults(func=handle_environment)


def handle_environment(args):
    if args.action == 'list':
        data = client.get_environments()
        print('{:10}{:32}{:32}'.format('BUILD', 'NAME', 'SHA256'))
        print("="*74)
        for row in data:
            name = row['name']
            build_id = row['build_id']
            sha256 = row.get('specification', {}).get('sha256')
            print(f'{build_id:<10}{name:32}{sha256[:32]:32}')

    elif args.action == 'create':
        with open(args.filename) as f:
            data = yaml.safe_load(f)
        client.post_specification(data)

    elif args.action == 'list-packages':
        if not args.name:
            print("Please supply an environment name")
            sys.exit(0)

        data = client.get_environment_packages(name=args.name)
        print('{:32}{:16}{:48}{:32}'.format('NAME', 'VERSION', 'LICENSE', 'SHA-256'))
        print("="*128)
        pkgs = data['specification']['builds'][0]['packages']
        for pkg in pkgs:
            name = pkg['name']
            version = pkg['version']
            license = pkg['license']
            sha = pkg['sha256']
            print(f'{name:32}{version:16}{license:48}{sha:32}')

