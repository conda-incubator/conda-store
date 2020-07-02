import argparse
import logging
import pathlib
import time

from conda_store.logging import init_logging
from conda_store.environments import discover_environments
from conda_store.build import conda_build
from conda_store.utils import free_disk_space
from conda_store.ui import start_ui_server
from conda_store.registry import start_registry_server
from conda_store.data_model import DatabaseManager, register_environment, number_schedulable_conda_builds, number_queued_conda_builds, claim_conda_build

logger = logging.getLogger(__name__)


def init_cli():
    parser = argparse.ArgumentParser(description='declarative conda environments on filesystem')
    subparser = parser.add_subparsers(help='sub-command help')
    init_build_cli(subparser)
    init_ui_cli(subparser)
    init_registry_cli(subparser)

    args = parser.parse_args()
    args.func(args)


def init_build_cli(subparser):
    parser = subparser.add_parser('build', help='build conda environments on filesystem')
    parser.add_argument('-p', '--paths', action='append', help='input paths for environments directories(non-recursive) and filenames', required=False)
    parser.add_argument('-s', '--store', type=str, default='.conda-store', help='directory for conda-store state')
    parser.add_argument('-o', '--output', type=str, help='output directory for symlinking conda environment builds', required=True)
    parser.add_argument('--poll-interval', type=int, default=10, help='poll interval to check environment directory for new environments')
    parser.add_argument('--uid', type=int, help='uid to assign to built environments')
    parser.add_argument('--gid', type=int, help='gid to assign to built environments')
    parser.add_argument('--permissions', type=str, help='permissions to assign to built environments')
    parser.add_argument('--storage-threshold', type=int, default=(5 * (2**30)), help='emit warning when free disk space drops below threshold bytes')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_build)


def init_ui_cli(subparser):
    parser = subparser.add_parser('ui', help='serve ui for conda build')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address to bind run conda-store ui')
    parser.add_argument('--port', type=int, default=5000, help='port to run conda-store ui')
    parser.add_argument('-s', '--store', type=str, default='.conda-store', help='directory for conda-store state')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_ui)


def init_registry_cli(subparser):
    parser = subparser.add_parser('registry', help='serve registry for conda build')
    parser.add_argument('--address', type=str, default='0.0.0.0', help='address to bind run conda-store registry')
    parser.add_argument('--port', type=int, default=5001, help='port to run conda-store registry')
    parser.add_argument('-s', '--store', type=str, default='.conda-store-cache', help='directory for conda-store state')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_registry)


def handle_ui(args):
    init_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    start_ui_server(store_directory, args.address, args.port)


def handle_registry(args):
    init_logging(args.verbose)

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    start_registry_server(store_directory, args.address, args.port)


def handle_build(args):
    init_logging(args.verbose)
    logger.info(f'polling interval set to {args.poll_interval} seconds')

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)

    output_directory = pathlib.Path(args.output).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    dbm = DatabaseManager(store_directory)

    while True:
        environments = discover_environments(args.paths)
        for environment in environments:
            register_environment(dbm, environment, output_directory)

        num_queued_builds = number_queued_conda_builds(dbm)
        if num_queued_builds > 0:
            logger.info(f'number of queued conda builds {num_queued_builds}')

        if free_disk_space(store_directory) < args.storage_threshold:
            logger.warning(f'free disk space={args.storage_threshold:g} [bytes] bellow storage threshold')

        num_schedulable_builds = number_schedulable_conda_builds(dbm)
        if num_schedulable_builds > 0:
            logger.info(f'number of schedulable conda builds {num_schedulable_builds}')
            conda_build(dbm, args.permissions, args.uid, args.gid)
        else:
            time.sleep(args.poll_interval)
