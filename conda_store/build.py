import os
import shutil
import logging
import subprocess
import pathlib
import stat
import tempfile
import traceback
import sys
import time
import hashlib
import gzip
import json

import yaml

from conda_store.utils import timer, chmod, chown, symlink, disk_usage, free_disk_space
from conda_store.data_model.base import DatabaseManager
from conda_store.data_model import build, package, api
from conda_store.data_model.conda_store import initialize_conda_store_state, calculate_storage_metrics
from conda_store.environments import discover_environments
from conda_store.conda import conda_list, conda_pack
from conda_store.storage import S3Storage, LocalStorage


logger = logging.getLogger(__name__)


def start_conda_build(store_directory, output_directory, paths, permissions, uid, gid, storage_threshold, storage_backend, poll_interval):
    dbm = DatabaseManager(store_directory)

    if storage_backend == 's3':
        storage_manager = S3Storage()
    else: # filesystem
        # storage_manager = LocalStorage(store_directory / 'storage', 'http://..../')
        raise NotImplementedError('filesystem as a storage_manager not implemented')

    initialize_conda_store_state(dbm)
    calculate_storage_metrics(dbm, store_directory)
    package.update_conda_channels(dbm)

    logger.info(f'polling interval set to {poll_interval} seconds')
    while True:
        environments = discover_environments(paths)
        for environment in environments:
            build.register_environment(dbm, environment)

        num_queued_builds = build.number_queued_conda_builds(dbm)
        if num_queued_builds > 0:
            logger.info(f'number of queued conda builds {num_queued_builds}')

        if free_disk_space(store_directory) < storage_threshold:
            logger.warning(f'free disk space={storage_threshold:g} [bytes] below storage threshold')

        num_schedulable_builds = build.number_schedulable_conda_builds(dbm)
        if num_schedulable_builds > 0:
            logger.info(f'number of schedulable conda builds {num_schedulable_builds}')
            conda_build(dbm, storage_manager, output_directory, permissions, uid, gid)
            calculate_storage_metrics(dbm, store_directory)
        else:
            time.sleep(poll_interval)


def conda_build(dbm, storage_manager, output_directory, permissions=None, uid=None, gid=None):
    build_id, name, spec, sha256, store_path = build.claim_conda_build(dbm)
    try:
        environment_store_directory = pathlib.Path(store_path)
        environment_install_directory = pathlib.Path(output_directory) / name

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
                        log_key = api.get_build_log_key(dbm, build_id)
                        storage_manager.set(log_key, e.output.encode('utf-8'), content_type='text/plain')
                        build.update_conda_build_failed(dbm, build_id)
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

        packages = conda_list(environment_store_directory)

        size = disk_usage(environment_store_directory)

        build_conda_archive(dbm, storage_manager, environment_store_directory, build_id)
        build_docker_image(storage_manager, environment_store_directory, name, sha256)

        log_key = api.get_build_log_key(dbm, build_id)
        storage_manager.set(log_key, output.encode('utf-8'), content_type='text/plain')
        build.update_conda_build_completed(dbm, build_id, packages, size)
    except Exception as e:
        logger.exception(e)
        log_key = api.get_build_log_key(dbm, build_id)
        storage_manager.set(log_key, traceback.format_exc().encode('utf-8'), content_type='text/plain')
        build.update_conda_build_failed(dbm, build_id)
    except BaseException as e:
        logger.error(f'exception {e.__class__.__name__} caught causing build={build_id} to be rescheduled')
        log_key = api.get_build_log_key(dbm, build_id)
        storage_manager.set(log_key, traceback.format_exc().encode('utf-8'), content_type='text/plain')
        build.update_conda_build_failed(dbm, build_id)
        sys.exit(1)


def build_conda_archive(dbm, storage_manager, conda_prefix, build_id):
    logger.info(f'packaging archive of conda environment={conda_prefix}')
    with tempfile.TemporaryDirectory() as tmpdir:
        output_filename = pathlib.Path(tmpdir) / 'environment.tar.gz'
        conda_pack(prefix=conda_prefix, output=output_filename)
        archive_key = api.get_build_archive_key(dbm, build_id)
        storage_manager.fset(archive_key, output_filename, content_type='application/gzip')


def build_docker_image(storage_manager, conda_prefix, name, sha256):
    from conda_docker.conda import (
        build_docker_environment_image,
        find_user_conda,
        conda_info,
        precs_from_environment_prefix,
        fetch_precs
    )
    logger.info(f'creating docker archive of conda environment={conda_prefix}')

    user_conda = find_user_conda()
    info = conda_info(user_conda)
    download_dir = info["pkgs_dirs"][0]
    precs = precs_from_environment_prefix(
        conda_prefix,
        download_dir,
        user_conda)
    records = fetch_precs(download_dir, precs)
    image = build_docker_environment_image(
        base_image='frolvlad/alpine-glibc:latest',
        output_image=f'{name}:{sha256}',
        records=records,
        default_prefix=info["default_prefix"],
        download_dir=download_dir,
        user_conda=user_conda,
        channels_remap=info.get("channels_remap", []),
        layering_strategy="layered",
    )

    manifest = {
        'schemaVersion': 2,
        'mediaType': 'application/vnd.docker.distribution.manifest.v2+json',
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": None,
            "digest": None,
        },
        "layers": [],
    }

    for layer in image.layers:
        content_hash = hashlib.sha256(layer.content).hexdigest()
        content_compressed = gzip.compress(layer.content)
        storage_manager.set(f'docker/blobs/{content_hash}', content_compressed, content_type='application/gzip')
        manifest['layers'].append({
            'mediaType': 'application/vnd.docker.image.rootfs.diff.tar.gzip',
            'size': len(content_compressed),
            'digest': f'sha256:{content_hash}'
        })

    storage_manager.set(f'docker/manifest/{name}/{sha256}', json.dumps(manifest).encode('utf-8'), content_type='application/vnd.docker.distribution.manifest.v1+json')
    logger.info(f'built docker image: {image.name}:{image.tag} layers={len(image.layers)}')
