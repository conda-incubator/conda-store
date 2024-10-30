# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import contextlib
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import AnyStr

from filelock import FileLock


class CondaStoreError(Exception):
    @property
    def message(self):
        return self.args[0]


class BuildPathError(CondaStoreError):
    pass


def symlink(source, target):
    # Multiple builds call this, so this lock avoids race conditions on unlink
    # and symlink operations
    with FileLock(f"{target}.lock"):
        try:
            os.unlink(target)
        except FileNotFoundError:
            pass
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


@contextlib.contextmanager
def chdir(directory: pathlib.Path):
    current_directory = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(current_directory)


def du(path):
    """
    Pure Python equivalent of du -sb
    Based on https://stackoverflow.com/a/55648984/161801
    """
    if os.path.islink(path) or os.path.isfile(path):
        return os.lstat(path).st_size
    nbytes = 0
    seen = set()
    for dirpath, dirnames, filenames in os.walk(path):
        nbytes += os.lstat(dirpath).st_size
        for f in filenames:
            fp = os.path.join(dirpath, f)
            st = os.lstat(fp)
            if st.st_ino in seen:
                continue
            seen.add(st.st_ino)  # adds inode to seen list
            nbytes += st.st_size  # adds bytes to total
        for d in dirnames:
            dp = os.path.join(dirpath, d)
            if os.path.islink(dp):
                nbytes += os.lstat(dp).st_size
    return nbytes


def disk_usage(path: pathlib.Path):
    if sys.platform == "darwin":
        cmd = ["du", "-sAB1", str(path)]
    elif sys.platform == "linux":
        cmd = ["du", "-sb", str(path)]
    else:
        return str(du(path))

    output = subprocess.check_output(cmd, encoding="utf-8").split()[0]
    if sys.platform == "darwin":
        # mac du does not have the -b option to return bytes
        output = str(int(output) * 512)
    return output


@contextlib.contextmanager
def timer(logger, prefix):
    start_time = time.time()
    yield
    logger.info(f"{prefix} took {time.time() - start_time:.3f} [s]")


# conda-lock defines Channel.used_env_vars as frozenset. But frozenset is not
# serializable to JSON, so this creates a custom JSON encoder to handle this
# type
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, frozenset):
            return list(obj)
        return super().default(obj)


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
    json_blob = json.dumps(recursive_sort(v), cls=CustomJSONEncoder)
    return hashlib.sha256(json_blob.encode("utf-8")).hexdigest()


def callable_or_value(v, *args, **kwargs):
    if callable(v):
        return v(*args, **kwargs)
    return v


def compile_arn_sql_like(
    arn: str, allowed_regex: re.Pattern[AnyStr]
) -> tuple[str, str]:
    """Turn an arn into a string suitable for use in a SQL LIKE statement.

    Parameters
    ----------
    arn : str
        String which matches namespaces and environments. For example:

            */*          matches all environments
            */team       matches all environments named 'team' in any namespace

    allowed_regex : re.Pattern[AnyStr]
        Regex to use to match the ARN.

    Returns
    -------
    tuple[str, str]
        (namespace regex, environment regex) to match in a sql LIKE statement.
        See conda_store_server.server.auth.Authentication.filter_environments
        for usage.
    """
    match = allowed_regex.match(arn)
    if match is None:
        raise ValueError(
            "Could not find a match for the requested " f"namespace/environment={arn}"
        )

    return (
        re.sub(r"\*", "%", match.group(1)),
        re.sub(r"\*", "%", match.group(2)),
    )
