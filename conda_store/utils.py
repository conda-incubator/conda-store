import os
import re
import hashlib
import subprocess
import contextlib
import time


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


def disk_usage(path):
    return subprocess.check_output(['du', '-sb', path], encoding='utf-8').split()[0]


def free_disk_space(path):
    disk = os.statvfs(str(path))
    return disk.f_bavail * disk.f_frsize
