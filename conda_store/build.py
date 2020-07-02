import os
import shutil
import logging
import subprocess
import pathlib
import stat
import tempfile
import traceback
import sys

import yaml

from conda_store.utils import timer, chmod, chown, symlink, disk_usage
from conda_store.data_model import (
    claim_conda_build,
    update_conda_build_completed,
    update_conda_build_failed
)

logger = logging.getLogger(__name__)


def conda_build(dbm, permissions=None, uid=None, gid=None):
    build_id, spec, store_path, install_path = claim_conda_build(dbm)
    try:
        environment_store_directory = pathlib.Path(store_path)
        environment_install_directory = pathlib.Path(install_path)

        # environment installation is an atomic process if a symlink at
        # "install_directory/environment_name" points to
        # "store_directory/environment_hash" installation is guarenteed to
        # have succeeded otherwise conda build is restarted
        # this is robust and the same concept that nixos uses
        if environment_install_directory.is_symlink() and \
           environment_store_directory.is_dir() and \
           environment_install_directory.resolve() == environment_store_directory:
            logger.debug(f'found cached {environment_store_directory} symlinked to {environment_install_directory}')
        else:
            logger.info(f'building {environment_store_directory} symlinked to {environment_install_directory}')

            logger.info(f'previously unfinished build of {environment_store_directory} cleaning directory')
            if environment_store_directory.is_dir():
                shutil.rmtree(str(environment_store_directory))

            with timer(logger, f'building {environment_store_directory}'):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_environment_filename = pathlib.Path(tmpdir) / 'environment.yaml'
                    with tmp_environment_filename.open('w') as f:
                        yaml.dump(spec, f)
                    args = ['conda', 'env', 'create', '-p', environment_store_directory, '-f', tmp_environment_filename]
                    try:
                        output = subprocess.check_output(args, stderr=subprocess.STDOUT, encoding='utf-8')
                    except subprocess.CalledProcessError as e:
                        update_conda_build_failed(dbm, build_id, e.output)
                        return

            symlink(environment_store_directory, environment_install_directory)

        # modify permissions, uid, gid if they do not match
        stat_info = os.stat(environment_store_directory)
        if permissions is not None and oct(stat.S_IMODE(stat_info.st_mode))[-3:] != str(permissions):
            logger.info(f'modifying permissions of {environment_store_directory} to permissions={permissions}')
            with timer(logger, f'chmod of {environment_store_directory}'):
                chmod(environment_store_directory, permissions)

        if uid is not None and gid is not None and (str(uid) != str(stat_info.st_uid) or str(gid) != str(stat_info.st_gid)):
            logger.info(f'modifying permissions of {environment_store_directory} to uid={uid} and gid={gid}')
            with timer(logger, f'chown of {environment_store_directory}'):
                chown(environment_store_directory, uid, gid)

        size = disk_usage(environment_store_directory)

        update_conda_build_completed(dbm, build_id, output, size)
    except Exception as e:
        logger.exception(e)
        update_conda_build_failed(dbm, build_id, traceback.format_exc())
    except BaseException as e:
        logger.error(f'exception {e.__class__.__name__} caught causing build={build_id} to be rescheduled')
        update_conda_build_failed(dbm, build_id, traceback.format_exc())
        sys.exit(1)
