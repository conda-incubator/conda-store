import os
import re
import subprocess
import contextlib
import time
import hashlib
import json


class CondaStoreError(Exception):
    @property
    def message(self):
        return self.args[0]


def symlink(source, target):
    if os.path.islink(target):
        os.unlink(target)
    os.symlink(source, target)


def chmod(directory, permissions):
    if re.fullmatch("[0-7]{3}", permissions) is None:
        raise ValueError(
            f"chmod permissions={permissions} not 3 integer values between 0-7"
        )

    subprocess.check_output(["chmod", "-R", str(permissions), directory])


def chown(directory, uid, gid):
    if re.fullmatch(r"\d+", str(uid)) is None:
        raise ValueError(f"chown uid={uid} not integer value")

    if re.fullmatch(r"\d+", str(gid)) is None:
        raise ValueError(f"chown gid={gid} not integer value")

    subprocess.check_output(["chown", "-R", f"{uid}:{gid}", directory])


def disk_usage(path):
    return subprocess.check_output(["du", "-sb", path], encoding="utf-8").split()[0]


@contextlib.contextmanager
def timer(logger, prefix):
    start_time = time.time()
    yield
    logger.info(f"{prefix} took {time.time() - start_time:.3f} [s]")


def recursive_sort(v):
    """Recursively sort a nested python objects of lists, dicts,
    strings, ints, and floats

    """

    def sort_key(v):
        if isinstance(v, (list, dict, tuple)):
            return str(type(v))
        return f"{type(v)}-{v}"

    if isinstance(v, dict):
        sorted_keys = sorted(v.keys(), key=sort_key)
        return {k: recursive_sort(v[k]) for k in sorted_keys}
    elif isinstance(v, (tuple, list)):
        sorted_items = sorted(v, key=sort_key)
        return [recursive_sort(_) for _ in sorted_items]
    return v


def datastructure_hash(v):
    json_blob = json.dumps(recursive_sort(v))
    return hashlib.sha256(json_blob.encode("utf-8")).hexdigest()
