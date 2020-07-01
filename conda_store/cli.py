import argparse
import logging
import pathlib
import time

from conda_store.logging import init_logging
from conda_store.environments import discover_environments
from conda_store.build import conda_build
from conda_store.utils import free_disk_space

logger = logging.getLogger(__name__)


def init_cli():
    parser = argparse.ArgumentParser(description='declarative conda environments on filesystem')
    parser.add_argument('-p', '--paths', action='append', help='input paths for environments directories(non-recursive) and filenames', required=False)
    parser.add_argument('-s', '--store', type=str, default='.conda-store-cache', help='directory for storing environments and logs')
    parser.add_argument('-o', '--output', type=str, help='output directory for symlinking conda environment builds', required=True)
    parser.add_argument('--poll-interval', type=int, default=10, help='poll interval to check environment directory for new environments')
    parser.add_argument('--uid', type=int, help='uid to assign to built environments')
    parser.add_argument('--gid', type=int, help='gid to assign to built environments')
    parser.add_argument('--permissions', type=str, help='permissions to assign to built environments')
    parser.add_argument('--storage-threshold', type=int, default=(5 * (2**30)), help='emit warning when free disk space drops below threshold bytes')
    parser.add_argument('--verbose', action='store_true', help='enable debug logging')
    parser.set_defaults(func=handle_build)

    args = parser.parse_args()
    args.func(args)


def handle_build(args):
    init_logging(args.verbose)
    logger.info(f'polling interval set to {args.poll_interval} seconds')

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)
    (store_directory / '.logs').mkdir(parents=True, exist_ok=True)

    output_directory = pathlib.Path(args.output).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    while True:
        environments = discover_environments(args.paths)
        logger.debug(f'found {len(environments)} to build')

        if free_disk_space(store_directory) < args.storage_threshold:
            logger.warning(f'free disk space={args.storage_threshold:g} [bytes] bellow storage threshold')

        for environment in environments:
            filename = environment['filename']
            conda_build(filename, output_directory, store_directory, args.permissions, args.uid, args.gid)

        time.sleep(args.poll_interval)
