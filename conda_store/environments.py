import pathlib
import yaml
import logging
import datetime

logger = logging.getLogger(__name__)


def is_environment_file(filename):
    if str(filename).endswith('.yaml') or str(filename).endswith('.yml'):
        return validate_environment(filename)
    else:
        return False


def validate_environment(filename):
    with filename.open() as f:
        data = yaml.safe_load(f)

    if 'name' not in data:
        logger.error(f'conda environment filename={filename} requires name')
        return False
    elif 'dependencies' not in data:
        logger.error(f'conda environment filename={filename} does not specify any dependencies')
        return False

    return True


def parse_environment(filename):
    with filename.open() as f:
        data = yaml.safe_load(f)

    return {
        'filename': filename.resolve(),
        'name': data['name'],
        'last_modified': datetime.datetime.fromtimestamp(filename.lstat().st_mtime),
        'data': data,
        'editable': False
    }


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
