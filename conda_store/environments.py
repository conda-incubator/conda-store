import pathlib
import logging
import datetime
import hashlib
import json

import yaml

logger = logging.getLogger(__name__)


def is_environment_file(filename):
    if str(filename).endswith('.yaml') or str(filename).endswith('.yml'):
        with filename.open() as f:
            return validate_environment(yaml.safe_load(f))
    else:
        return False


def environment_hash(spec):
    return hashlib.sha256(json.dumps(spec).encode('utf-8')).hexdigest()


def validate_environment(spec, filename=None):
    if 'name' not in spec:
        logger.error(f'conda environment filename={filename} requires name')
        return False
    elif 'dependencies' not in spec:
        logger.error(f'conda environment name={spec["name"]} filename={filename} does not specify dependencies')
        return False

    return True


def parse_environment(spec, filename=None):
    with filename.open() as f:
        data = yaml.safe_load(f)

    return {
        'filename': filename.resolve(),
        'name': data['name'],
        'last_modified': datetime.datetime.fromtimestamp(filename.lstat().st_mtime),
        'data': data,
        'editable': False
    }


def lock_environment(channels, dependencies, platform="linux-64"):
    args = [
        "conda",
        "create",
        "--prefix",
        pathlib.Path(conda_pkgs_dir()).joinpath("prefix"),
        "--override-channels",
        "--dry-run",
        "--json",
    ]
    for channel in channels:
        args.extend(["--channel", channel])
        if channel == "defaults" and platform in {"win-64", "win-32"}:
            # msys2 is a windows-only channel that conda automatically
            # injects if the host platform is Windows. If our host
            # platform is not Windows, we need to add it manually
            args.extend(["--channel", "msys2"])
    args.extend(specs)

    proc = subprocess.run(
        args,
        env=conda_env_override(platform),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf8",
    )
    try:
        proc.check_returncode()
    except subprocess.CalledProcessError:
        try:
            err_json = json.loads(proc.stdout)
            message = err_json["message"]
        except json.JSONDecodeError as e:
            print(f"Failed to parse json, {e}")
            message = ""

        print(f"Could not lock the environment for platform {platform}")
        if message:
            print(message)
        print(f"    Command: {proc.args}")
        if proc.stdout:
            print(f"    STDOUT:\n{proc.stdout}")
        if proc.stderr:
            print(f"    STDOUT:\n{proc.stderr}")
        sys.exit(1)

    return json.loads(proc.stdout)


def discover_environments(paths):
    environments = []
    for path in paths:
        path = pathlib.Path(path).resolve()
        if path.is_file() and is_environment_file(path):
            logger.debug(f'discoverd environment filename={path}')
            environments.append(parse_environment(path))
        elif path.is_dir():
            for _path in path.glob('*'):
                if is_environment_file(_path):
                    logger.debug(f'discoverd environment filename={_path}')
                    environments.append(parse_environment(_path))
    return environments
