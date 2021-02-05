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

from conda_store import api, utils, conda
from conda_store.environment import discover_environments


logger = logging.getLogger(__name__)


def start_conda_build(conda_store, paths, storage_threshold, poll_interval):
    logger.info(f'polling interval set to {poll_interval} seconds')
    while True:
        environments = discover_environments(paths)
        for environment in environments:
            conda_store.register_environment(environment)

        num_queued_builds = api.get_num_queued_builds(conda_store.db)
        if num_queued_builds > 0:
            logger.info(f'number of queued conda builds {num_queued_builds}')

        disk_usage = conda_store.update_storage_metrics()
        if disk_usage.free < storage_threshold:
            logger.warning(f'free disk space={storage_threshold:g} [bytes] below storage threshold')

        num_schedulable_builds = api.get_num_schedulable_builds(conda_store.db)
        if num_schedulable_builds > 0:
            logger.info(f'number of schedulable conda builds {num_schedulable_builds}')
            conda_build(conda_store)
            time.sleep(1)
        else:
            time.sleep(poll_interval)


def conda_build(conda_store):
    build = conda_store.claim_build()
    store_directory = pathlib.Path(
        conda_store.configuration.store_directory)
    environment_directory = pathlib.Path(
        conda_store.configuration.environment_directory)
    build_path = build.build_path(store_directory)
    environment_path = build.environment_path(environment_directory)
    try:
        # environment installation is an atomic process if a symlink at
        # "install_directory/environment_name" points to
        # "store_directory/environment_hash" installation is guarenteed to
        # have succeeded otherwise conda build is restarted
        # this is robust and the same concept that nixos uses
        if environment_path.is_symlink() and \
           build_path.is_dir() and \
           environment_path.resolve() == build_path:
            logger.debug(f'found cached {build_path} symlinked to {environment_path}')
        else:
            logger.info(f'building {build_path} symlinked to {environment_path}')

            logger.info(f'previously unfinished build of {build_path} cleaning directory')
            if build_path.is_dir():
                shutil.rmtree(str(build_path))

            with utils.timer(logger, f'building {build_path}'):
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmp_environment_filename = pathlib.Path(tmpdir) / 'environment.yaml'
                    with tmp_environment_filename.open('w') as f:
                        yaml.dump(build.specification.spec, f)
                    try:
                        output = build_conda_install(conda_store, build_path, tmp_environment_filename)
                    except subprocess.CalledProcessError as e:
                        conda_store.set_build_failed(build, e.output.encode('utf-8'))
                        return

        utils.symlink(build_path, environment_path)

        # modify permissions, uid, gid if they do not match
        stat_info = os.stat(build_path)
        permissions = conda_store.configuration.default_permissions
        uid = conda_store.configuration.default_uid
        gid = conda_store.configuration.default_gid

        if permissions is not None and \
           oct(stat.S_IMODE(stat_info.st_mode))[-3:] != str(permissions):
            logger.info(f'modifying permissions of {build_path} to permissions={permissions}')
            with utils.timer(logger, f'chmod of {build_path}'):
                utils.chmod(build_path, permissions)

        if uid is not None and gid is not None and (str(uid) != str(stat_info.st_uid) or str(gid) != str(stat_info.st_gid)):
            logger.info(f'modifying permissions of {build_path} to uid={uid} and gid={gid}')
            with utils.timer(logger, f'chown of {build_path}'):
                utils.chown(build_path, uid, gid)

        packages = conda.conda_list(build_path)
        build.size = utils.disk_usage(build_path)

        build_conda_pack(conda_store, build_path, build)
        build_docker_image(conda_store, build_path, build)

        conda_store.set_build_completed(build, output.encode('utf-8'), packages)
    except Exception as e:
        logger.exception(e)
        conda_store.set_build_failed(build, traceback.format_exc().encode('utf-8'))
    except BaseException as e:
        logger.error(f'exception {e.__class__.__name__} caught causing build={build_id} to be rescheduled')
        conda_store.set_build_failed(build, traceback.format_exc().encode('utf-8'))
        sys.exit(1)


def build_conda_install(conda_store, build_path, environment_filename):
    args = ['conda', 'env', 'create', '-p', str(build_path), '-f', str(environment_filename)]
    return subprocess.check_output(args, stderr=subprocess.STDOUT, encoding='utf-8')


def build_conda_pack(conda_store, conda_prefix, build):
    logger.info(f'packaging archive of conda environment={conda_prefix}')
    with tempfile.TemporaryDirectory() as tmpdir:
        output_filename = pathlib.Path(tmpdir) / 'environment.tar.gz'
        conda.conda_pack(prefix=conda_prefix, output=output_filename)
        conda_store.storage.fset(
            build.conda_pack_key,
            output_filename,
            content_type='application/gzip')


def build_docker_image(conda_store, conda_prefix, build):
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
        output_image=f'{build.specification.name}:{build.specification.sha256}',
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
        conda_store.storage.set(build.docker_blob_key(content_hash), content_compressed, content_type='application/gzip')
        manifest['layers'].append({
            'mediaType': 'application/vnd.docker.image.rootfs.diff.tar.gzip',
            'size': len(content_compressed),
            'digest': f'sha256:{content_hash}'
        })

    conda_store.storage.set(
        build.docker_manifest_key,
        json.dumps(manifest).encode('utf-8'),
        content_type='application/vnd.docker.distribution.manifest.v1+json')
    logger.info(f'built docker image: {image.name}:{image.tag} layers={len(image.layers)}')
