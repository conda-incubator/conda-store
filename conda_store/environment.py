import pathlib
import logging
import hashlib
import json

import yaml

from conda_store import utils

logger = logging.getLogger(__name__)


def validate_environment(specification, filename=None):
    if not isinstance(specification, dict):
        logger.error(f'conda environment filename={filename} must be a dictionary')
        return False
    elif 'name' not in specification:
        logger.error(f'conda environment filename={filename} requires name')
        return False
    elif 'dependencies' not in specification:
        logger.error(f'conda environment name={specification["name"]} filename={filename} does not specify dependencies')
        return False
    return True


def is_environment_file(filename):
    if str(filename).endswith('.yaml') or str(filename).endswith('.yml'):
        with filename.open() as f:
            return validate_environment(yaml.safe_load(f))
    else:
        return False


def discover_environments(paths):
    environments = []
    for path in paths:
        path = pathlib.Path(path).resolve()
        if path.is_file() and is_environment_file(path):
            logger.debug(f'discoverd environment filename={path}')
            environments.append(path)
        elif path.is_dir():
            for _path in path.glob('*'):
                if is_environment_file(_path):
                    logger.debug(f'discoverd environment filename={_path}')
                    environments.append(_path)
    return environments
