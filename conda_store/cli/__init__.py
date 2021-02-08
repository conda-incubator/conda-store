import argparse

from conda_store.logging import initialize_logging
from conda_store.cli.build import initialize_build_cli
from conda_store.cli.server import initialize_server_cli


def initialize_cli():
    parser = argparse.ArgumentParser(description='declarative conda environments')
    subparser = parser.add_subparsers(help='sub-command help')
    initialize_build_cli(subparser)
    initialize_server_cli(subparser)

    args = parser.parse_args()
    initialize_logging(args.verbose)

    args.func(args)
