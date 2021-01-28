import pathlib
import logging
import datetime
import hashlib
import json

import yaml

from conda_store.data_model.base import Environment

logger = logging.getLogger(__name__)


def is_environment_file(filename):
    if str(filename).endswith('.yaml') or str(filename).endswith('.yml'):
        with filename.open() as f:
            return validate_environment(yaml.safe_load(f))
    else:
        return False


def validate_environment(spec, filename=None):
    if not isinstance(spec, dict):
        logger.error(f'conda environment filename={filename} must be a dictionary')
        return False
    elif 'name' not in spec:
        logger.error(f'conda environment filename={filename} requires name')
        return False
    elif 'dependencies' not in spec:
        logger.error(f'conda environment name={spec["name"]} filename={filename} does not specify dependencies')
        return False

    return True


def parse_environment_filename(filename):
    with filename.open() as f:
        spec = yaml.safe_load(f)
    environment = parse_environment_spec(spec)
    environment.filename = str(filename.resolve())
    environment.created_on = datetime.datetime.fromtimestamp(
        filename.lstat().st_mtime)
    return environment


def parse_environment_spec(spec):
    # return row that fits data_model table "enviornment"
    return Environment(
        name=spec['name'],
        created_on=datetime.datetime.now(),
        filename=None,
        spec=spec,
        spec_sha256=environment_hash(spec)
    )


def environment_hash(spec):
    return hashlib.sha256(json.dumps(spec).encode('utf-8')).hexdigest()


def discover_environments(paths):
    environments = []
    for path in paths:
        path = pathlib.Path(path).resolve()
        if path.is_file() and is_environment_file(path):
            logger.debug(f'discoverd environment filename={path}')
            environments.append(parse_environment_filename(path))
        elif path.is_dir():
            for _path in path.glob('*'):
                if is_environment_file(_path):
                    logger.debug(f'discoverd environment filename={_path}')
                    environments.append(parse_environment_filename(_path))
    return environments
