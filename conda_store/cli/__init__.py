import argparse

from conda_store.logging import initialize_logging
from conda_store.cli.build import initialize_build_cli
from conda_store.cli.server import initialize_server_cli
from conda_store.cli.env import initialize_env_cli


def initialize_cli():
    parser = argparse.ArgumentParser(description="declarative conda environments")
    parser.add_argument("--verbose", action="store_true", help="enable debug logging")
    subparser = parser.add_subparsers(help="sub-command help")

    initialize_build_cli(subparser)
    initialize_server_cli(subparser)
    initialize_env_cli(subparser)

    args = parser.parse_args()
    initialize_logging(args.verbose)

    args.func(args)
