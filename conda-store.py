import stat
import re
import argparse
import datetime
import hashlib
import logging
import os
import pathlib
import subprocess
import time
import yaml
import shutil
import contextlib
import functools


logger = logging.getLogger(__name__)


# format: {buildsha: (last failed, timeout seconds)}
CONDA_FAILED_BUILDS = {}


def filename_hash(filename):
    with open(filename, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def symlink(source, target):
    if target.is_symlink():
        target.unlink()
    target.symlink_to(source)


def chmod(directory, permissions):
    if re.fullmatch('[0-7]{3}', permissions) is None:
        raise ValueError(f'chmod permissions={permissions} not 3 integer values between 0-7')

    subprocess.check_output(['chmod', '-R', str(permissions), str(directory)])


def chown(directory, uid, gid):
    if re.fullmatch('\d+', str(uid)) is None:
        raise ValueError(f'chown uid={uid} not integer value')

    if re.fullmatch('\d+', str(gid)) is None:
        raise ValueError(f'chown gid={gid} not integer value')

    subprocess.check_output(['chown', '-R', f'{uid}:{gid}', str(directory)])


@contextlib.contextmanager
def timer(logger, prefix):
    start_time = time.time()
    yield
    logger.info(f'{prefix} took {time.time() - start_time:.3f} [s]')


@contextlib.contextmanager
def extended_conda_environment(filename):
    """Extended conda build

    """
    pass


def conda_build(environment_filename, install_directory, store_directory, permissions=None, uid=None, gid=None):
    environment_name = yaml.safe_load(environment_filename.open())['name']

    environment_hash = filename_hash(environment_filename)
    environment_directory = store_directory / f'{environment_hash}-{environment_name}'
    environment_install_directory = install_directory / environment_name

    build_key = f'{environment_hash}-{environment_name}'
    log_filename = store_directory / '.logs' / f'{datetime.datetime.now()}-{build_key}.log'

    func = functools.partial(_conda_build, environment_name, environment_filename, environment_directory, environment_install_directory, permissions, uid, gid)
    run_with_exponential_backoff(build_key, log_filename, func)


def run_with_exponential_backoff(build_key, log_filename, func):
    """Run

    """
    global CONDA_FAILED_BUILDS

    if build_key in CONDA_FAILED_BUILDS:
        last_failed, timeout = CONDA_FAILED_BUILDS[build_key]

        # if timeout is less than time since last failure
        if (datetime.datetime.now() - last_failed).seconds < timeout:
            return None
        else:
            logger.info(f'build {build_key} starting again since past timeout of {timeout} seconds')

    try:
        return func()
        # if build succeeded and in failed builds remove
        if build_key in CONDA_FAILED_BUILDS:
            CONDA_FAILED_BUILDS.pop(build_key)
    except subprocess.CalledProcessError as e:
        # if build have previously failed double the timeout
        if build_key in CONDA_FAILED_BUILDS:
            last_failed, timeout = CONDA_FAILED_BUILDS[build_key]
            CONDA_FAILED_BUILDS[build_key] = (datetime.datetime.now(), timeout * 2)
            logger.error(f'build failed for {build_key} setting timeout={timeout * 2.0} [s]')
        # else set timeout to 10 second
        else:
            CONDA_FAILED_BUILDS[build_key] = (datetime.datetime.now(), 10.0)
            logger.error(f'build failed for {build_key} setting timeout={10.0} [s]')

        # write logs to store_directory
        with log_filename.open('wb') as f:
            f.write(e.stdout)


def _conda_build(environment_name, environment_filename, environment_directory, environment_install_directory, permissions, uid, gid):
    # environment installation is an atomic process if a symlink at
    # "install_directory/environment_name" points to
    # "store_directory/environment_hash" installation is guarenteed to
    # have succeeded otherwise conda build is restarted
    # this is robust and the same concept that nixos uses
    if environment_install_directory.is_symlink() and \
       environment_directory.is_dir() and \
       environment_install_directory.resolve() == environment_directory:
        logger.info(f'found cached {environment_name} in {environment_install_directory}')
    else:
        logger.info(f'building {environment_name} in {environment_install_directory}')

        logger.info(f'previously unfinished build of {environment_name} cleaning directory')
        if environment_directory.is_dir():
            shutil.rmtree(str(environment_directory))

        with timer(logger, f'building {environment_name}'):
            subprocess.check_output(['conda', 'env', 'create', '-p', environment_directory, '-f', environment_filename], stderr=subprocess.STDOUT)

        symlink(environment_directory, environment_install_directory)

    # modify permissions, uid, gid if they do not match
    stat_info = os.stat(environment_directory)
    if permissions is not None and oct(stat.S_IMODE(stat_info.st_mode))[-3:] != str(permissions):
        logger.info(f'modifying permissions of {environment_directory} to permissions={permissions}')
        with timer(logger, f'chmod of {environment_directory}'):
            chmod(environment_directory, permissions)

    if uid is not None and gid is not None and (str(uid) != str(stat_info.st_uid) or str(gid) != str(stat_info.st_gid)):
        logger.info(f'modifying permissions of {environment_directory} to uid={uid} and gid={gid}')
        with timer(logger, f'chown of {environment_directory}'):
            chown(environment_directory, uid, gid)


def check_environments(environment_directory):
    environments = []
    for filename in os.listdir(environment_directory):
        if filename.endswith('.yml') or filename.endswith('.yaml'):
            environments.append(environment_directory / filename)
    return environments


def main():
    init_logging()
    args = init_cli()

    logger.info(f'polling interval set to {args.poll_interval} seconds')

    store_directory = pathlib.Path(args.store).expanduser().resolve()
    store_directory.mkdir(parents=True, exist_ok=True)
    (store_directory / '.logs').mkdir(parents=True, exist_ok=True)

    output_directory = pathlib.Path(args.output).expanduser().resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    environment_directory = pathlib.Path(args.environments).expanduser().resolve()

    while True:
        environment_filenames = check_environments(environment_directory)
        logger.info(f'found {len(environment_filenames)} to build')

        for filename in environment_filenames:
            conda_build(filename, output_directory, store_directory, args.permissions, args.uid, args.gid)

        time.sleep(args.poll_interval)


def init_logging(level=logging.INFO):
    logging.basicConfig(level=level)


def init_cli():
    parser = argparse.ArgumentParser(description='declarative conda environments on filesystem')
    parser.add_argument('-e', '--environments', type=str, help='input directory for environments', required=True)
    parser.add_argument('-s', '--store', type=str, default='.conda-store-cache', help='directory for storing environments and logs')
    parser.add_argument('-o', '--output', type=str, help='output directory for symlinking conda environment builds', required=True)
    parser.add_argument('--poll-interval', type=int, default=10, help='poll interval to check environment directory for new environments')
    parser.add_argument('--uid', type=int, help='uid to assign to built environments')
    parser.add_argument('--gid', type=int, help='gid to assign to built environments')
    parser.add_argument('--permissions', type=str, help='permissions to assign to built environments')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
