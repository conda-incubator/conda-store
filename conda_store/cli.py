import argparse
import logging
import pathlib

from conda_store.logging import init_logging
from conda_store.build import start_conda_build
from conda_store.ui import start_ui_server
from conda_store.api import start_api_server
from conda_store.registry import start_registry_server

logger = logging.getLogger(__name__)


def init_cli():
    parser = argparse.ArgumentParser(description='declarative conda environments on filesystem')
    subparser = parser.add_subparsers(help='sub-command help')
    init_build_cli(subparser)
    init_api_cli(subparser)
    init_ui_cli(subparser)
    init_registry_cli(subparser)

    args = parser.parse_args()
    args.func(args)


def init_build_cli(subparser):
    parser = subparser.add_parser('build', help='build conda environments on filesystem')
    parser.add_argument('-s', '--store', type=str, default='.conda-store', help='directory for conda-store state')
    parser.add_argument('-o', '--output', type=str, help='output directory for symlinking conda environment builds', required=True)
    parser.add_argument('-p', '--paths', action='append', help='input paths for environments directories(non-recursive) and filenames', required=False)
    parser.add_argument('--uid', type=int, help='uid to assign to built environments')
    parser.add_argument('--gid', type=int, help='gid to assign to built environments')
    parser.add_argument('--permissions', type=str, help='permissions to assign to built environments')
    parser.add_argument('--storage-threshold', type=int, default=(5 * (2**30)), help='emit warning when free disk space drops below threshold bytes')
    parser.add_argument('--storage-backend', type=str, default='filesystem', choices=['filesystem', 's3'], help='backend for storing build artifacts. Production should use s3')
    parser.add_argument('--poll-interval', type=int, default=10, help='poll interval to check environment directory for new environments')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_build)


def handle_build(args):
    init_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)
    output_directory = pathlib.Path(args.output).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    start_conda_build(store_directory, output_directory, args.paths, args.permissions, args.uid, args.gid, args.storage_threshold, args.poll_interval)


def init_ui_cli(subparser):
    parser = subparser.add_parser('ui', help='serve ui for conda build')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address to bind run conda-store ui')
    parser.add_argument('--port', type=int, default=5000, help='port to run conda-store ui')
    parser.add_argument('-s', '--store', type=str, default='.conda-store', help='directory for conda-store state')
    parser.add_argument('--storage-backend', type=str, default='filesystem', choices=['filesystem', 's3'], help='backend for storing build artifacts. Production should use s3')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_ui)


def handle_ui(args):
    init_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    start_ui_server(store_directory, args.address, args.port)


def init_api_cli(subparser):
    parser = subparser.add_parser('api', help='serve api for conda build')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address to bind run conda-store api')
    parser.add_argument('--port', type=int, default=5001, help='port to run conda-store api')
    parser.add_argument('-s', '--store', type=str, default='.conda-store', help='directory for conda-store state')
    parser.add_argument('--storage-backend', type=str, default='filesystem', choices=['filesystem', 's3'], help='backend for storing build artifacts. Production should use s3')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_api)


def handle_api(args):
    init_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    start_api_server(store_directory, args.address, args.port)


def init_registry_cli(subparser):
    parser = subparser.add_parser('registry', help='serve registry for conda build')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address to bind run conda-store registry')
    parser.add_argument('--port', type=int, default=5002, help='port to run conda-store registry')
    parser.add_argument('-s', '--store', type=str, default='.conda-store-cache', help='directory for conda-store state')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_registry)


def handle_registry(args):
    init_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    start_registry_server(store_directory, args.address, args.port)
