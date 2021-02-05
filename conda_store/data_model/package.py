import logging

logger = logging.getLogger(__name__)


def link_packages_to_build(dbm, build_id, conda_packages):
    # TODO: add to build
    with dbm.transaction() as cursor:
        cursor.executemany('''
          INSERT INTO build_package
          SELECT
            ? AS build_id,
            conda_package.id AS conda_package_id
          FROM conda_package
          WHERE channel = ?
            AND subdir = ?
            AND name = ?
            AND version = ?
            AND build = ?
            AND build_number = ?
        ''', [(build_id, _['base_url'], _['platform'], _['name'], _['version'], _['build_string'], _['build_number']) for _ in conda_packages])
