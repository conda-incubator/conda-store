import argparse
import logging
import pathlib

from conda_store.logging import initialize_logging
from conda_store.app import CondaStore

logger = logging.getLogger(__name__)


def initialize_cli():
    parser = argparse.ArgumentParser(description='declarative conda environments on filesystem')
    subparser = parser.add_subparsers(help='sub-command help')
    initialize_build_cli(subparser)
    initialize_api_cli(subparser)
    initialize_ui_cli(subparser)
    initialize_registry_cli(subparser)

    args = parser.parse_args()
    args.func(args)


def initialize_build_cli(subparser):
    parser = subparser.add_parser('build', help='build conda environments on filesystem')
    parser.add_argument('-s', '--store', type=str, default='.conda-store', help='directory for conda-store state')
    parser.add_argument('-e', '--environment', type=str, help='environment directory for symlinking conda environment builds', required=True)
    parser.add_argument('-p', '--paths', action='append', help='input paths for environments directories(non-recursive) and filenames', required=False)
    parser.add_argument('--uid', type=int, help='uid to assign to built environments')
    parser.add_argument('--gid', type=int, help='gid to assign to built environments')
    parser.add_argument('--permissions', type=str, help='permissions to assign to built environments')
    parser.add_argument('--storage-threshold', type=int, default=(5 * (2**30)), help='emit warning when free disk space drops below threshold bytes')
    parser.add_argument('--storage-backend', type=str, default='s3', choices=['filesystem', 's3'], help='backend for storing build artifacts. Production should use s3')
    parser.add_argument('--poll-interval', type=int, default=10, help='poll interval to check environment directory for new environments')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_build)


def handle_build(args):
    from conda_store.build import start_conda_build

    initialize_logging(args.verbose)

    conda_store = CondaStore(
        store_directory=args.store,
        environment_directory=args.environment,
        database_url=None,
        storage_backend=args.storage_backend,
        default_permissions=args.permissions,
        default_uid=args.uid,
        default_gid=args.gid)

    start_conda_build(conda_store, args.paths, args.storage_threshold, args.poll_interval)


def initialize_ui_cli(subparser):
    parser = subparser.add_parser('ui', help='serve ui for conda build')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address to bind run conda-store ui')
    parser.add_argument('--port', type=int, default=5000, help='port to run conda-store ui')
    parser.add_argument('-s', '--store', type=str, default='.conda-store', help='directory for conda-store state')
    parser.add_argument('--storage-backend', type=str, default='s3', choices=['filesystem', 's3'], help='backend for storing build artifacts. Production should use s3')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_ui)


def handle_ui(args):
    from conda_store.server.ui import start_ui_server

    initialize_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    start_ui_server(store_directory, args.storage_backend, args.address, args.port)


def initialize_api_cli(subparser):
    parser = subparser.add_parser('api', help='serve api for conda build')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address to bind run conda-store api')
    parser.add_argument('--port', type=int, default=5001, help='port to run conda-store api')
    parser.add_argument('-s', '--store', type=str, default='.conda-store', help='directory for conda-store state')
    parser.add_argument('--storage-backend', type=str, default='filesystem', choices=['filesystem', 's3'], help='backend for storing build artifacts. Production should use s3')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_api)


def handle_api(args):
    from conda_store.server.api import start_api_server

    initialize_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    start_api_server(store_directory, args.address, args.port)


def initialize_registry_cli(subparser):
    parser = subparser.add_parser('registry', help='serve registry for conda build')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address to bind run conda-store registry')
    parser.add_argument('--port', type=int, default=5002, help='port to run conda-store registry')
    parser.add_argument('-s', '--store', type=str, default='.conda-store-cache', help='directory for conda-store state')
    parser.add_argument('--storage-backend', type=str, default='filesystem', choices=['filesystem', 's3'], help='backend for storing build artifacts. Production should use s3')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_registry)


def handle_registry(args):
    from conda_store.server.registry import start_registry_server

    initialize_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    start_registry_server(store_directory, args.storage_backend, args.address, args.port)


def init_env_cli(subparser):
    parser = subparser.add_parser('env', help='manage conda environments')
    parser.add_argument('action', choices=['create', 'list'], help='action to take on conda environments')
    parser.add_argument('-f', '--filename', help='conda environment filename to use')
    parser.set_defaults(func=handle_environment)


def handle_environment(args):
    if args.action == 'list':
        data = client.get_environments()
        print('{:10}{:32}{:32}'.format('BUILD', 'NAME', 'SHA256'))
        print("="*74)
        for row in data:
            print(f'{row["build_id"]:<10}{row["name"]:32}{row["spec_sha256"][:32]:32}')
    elif args.action == 'create':
        with open(args.filename) as f:
            data = yaml.safe_load(f)
        client.post_specification(data)
