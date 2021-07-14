import pathlib

import yaml
import pydantic

from conda_store_server import schema


def validate_environment(specification):
    try:
        specification = schema.CondaSpecification.parse_obj(specification)
        return True
    except pydantic.ValidationError:
        return False


def is_environment_file(filename):
    if str(filename).endswith(".yaml") or str(filename).endswith(".yml"):
        with filename.open() as f:
            return validate_environment(yaml.safe_load(f))
    else:
        return False


def discover_environments(paths):
    environments = []
    for path in paths:
        path = pathlib.Path(path).resolve()
        if path.is_file() and is_environment_file(path):
            environments.append(path)
        elif path.is_dir():
            for _path in path.glob("*"):
                if is_environment_file(_path):
                    environments.append(_path)
    return environments
