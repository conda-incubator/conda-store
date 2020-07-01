import os
import shutil
import functools
import datetime
import logging
import subprocess
import pathlib
import stat
import tempfile

import yaml

from conda_store.utils import filename_hash, timer, chmod, chown, symlink, timer


logger = logging.getLogger(__name__)


CONDA_FAILED_BUILDS = {}


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
        logger.debug(f'found cached {environment_name} in {environment_install_directory}')
    else:
        logger.info(f'building {environment_name} in {environment_install_directory}')

        logger.info(f'previously unfinished build of {environment_name} cleaning directory')
        if environment_directory.is_dir():
            shutil.rmtree(str(environment_directory))

        with timer(logger, f'building {environment_name}'):
            with tempfile.TemporaryDirectory() as tmpdir:
                # directory of environment.yaml must be writeable
                # https://github.com/Quansight/conda-store/issues/1
                tmp_environment_filename = pathlib.Path(tmpdir) / 'environment.yaml'
                shutil.copyfile(environment_filename, str(tmp_environment_filename))
                subprocess.check_output(['conda', 'env', 'create', '-p', environment_directory, '-f', tmp_environment_filename], stderr=subprocess.STDOUT)

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
