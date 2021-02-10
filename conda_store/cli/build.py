import pathlib
import logging

from conda_store.build import start_conda_build
from conda_store.app import CondaStore

logger = logging.getLogger(__name__)


def initialize_build_cli(subparser):
    parser = subparser.add_parser(
        "build", help="build conda environments on filesystem"
    )
    parser.add_argument(
        "-s",
        "--store",
        type=str,
        default=".conda-store",
        help="directory for conda-store state",
    )
    parser.add_argument(
        "-e",
        "--environment",
        type=str,
        help="environment directory for symlinking conda environment builds",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--paths",
        action="append",
        help="input paths for environments directories(non-recursive) and filenames",
        required=False,
    )
    parser.add_argument("--uid", type=int, help="uid to assign to built environments")
    parser.add_argument("--gid", type=int, help="gid to assign to built environments")
    parser.add_argument(
        "--permissions", type=str, help="permissions to assign to built environments"
    )
    parser.add_argument(
        "--storage-threshold",
        type=int,
        default=(5 * (2 ** 30)),
        help="emit warning when free disk space drops below threshold bytes",
    )
    parser.add_argument(
        "--storage-backend",
        type=str,
        default="s3",
        choices=["filesystem", "s3"],
        help="backend for storing build artifacts. Production should use s3",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="poll interval to check environment directory for new environments",
    )
    parser.set_defaults(func=handle_build)


def handle_build(args):
    conda_store = CondaStore(
        store_directory=args.store,
        database_url=None,
        storage_backend=args.storage_backend,
    )

    environment_directory = pathlib.Path(
        args.environment
        or conda_store.configuration.environment_directory
        or (conda_store.configuration.store_directory / "envs")
    ).resolve()
    if not environment_directory.is_dir():
        logger.info(f"creating directory environment_directory={environment_directory}")
        environment_directory.mkdir(parents=True)
    conda_store.configuration.environment_directory = str(environment_directory)

    if args.permissions:
        conda_store.configuration.default_permissions = args.permissions
    if args.uid:
        conda_store.configuration.default_uid = args.uid
    if args.gid:
        conda_store.configuration.default_gid = args.gid

    conda_store.update_storage_metrics()
    conda_store.update_conda_channels()

    start_conda_build(
        conda_store, args.paths, args.storage_threshold, args.poll_interval
    )
