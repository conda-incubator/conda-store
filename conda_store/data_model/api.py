import logging
import math

from conda_store.environments import parse_environment_spec, validate_environment
from conda_store.data_model.build import register_environment
from conda_store.data_model.base import BuildStatus
from conda_store import utils

logger = logging.getLogger(__name__)


def list_environments(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            environment.name,
            specification.spec_sha256,
            environment.build_id,
            build.store_path,
            build.size
          FROM environment
          LEFT JOIN specification ON environment.specification_id = specification.id
          LEFT JOIN build ON environment.build_id = build.id
          ORDER BY environment.name
        ''')
        return cursor.fetchall()


def get_environment(dbm, environment_name):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            environment.name,
            specification.spec_sha256,
            environment.build_id,
            build.store_path,
            build.size
          FROM environment
          LEFT JOIN specification ON environment.specification_id = specification.id
          LEFT JOIN build ON environment.build_id = build.id
          WHERE environment.name = ?
        ''', (environment_name,))
        result = cursor.fetchone()

        cursor.execute('''
          SELECT
            build.id,
            build.status
          FROM environment
          INNER JOIN specification ON environment.name = specification.name
          INNER JOIN build ON specification.id = build.specification_id
          WHERE environment.name = ?
        ''', (environment_name,))

        result['builds'] = [{'id': row['id'], 'status': row['status'].name} for row in cursor.fetchall()]
        return result


def list_specifications(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            name,
            created_on,
            filename,
            spec,
            spec_sha256
          FROM specification
        ''')
        return cursor.fetchall()


def post_specification(dbm, spec):
    if not validate_environment(spec):
        raise ValueError('Specification is not a valid conda environment')
    environment = parse_environment_spec(spec)
    register_environment(dbm, environment)


def get_specification(dbm, spec_sha256):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            specification.name,
            specification.created_on,
            specification.filename,
            specification.spec,
            (
              SELECT COUNT(*)
              FROM build
              INNER JOIN specification ON build.specification_id = specification.id
              WHERE specification.spec_sha256 = ?
            ) AS num_builds
          FROM specification
          WHERE specification.spec_sha256 = ?
        ''', (spec_sha256, spec_sha256))
        result = cursor.fetchone()

        cursor.execute('''
          SELECT
            build.id,
            build.status
          FROM build
          INNER JOIN specification ON build.specification_id = specification.id
          WHERE specification.spec_sha256 = ?
        ''', (spec_sha256,))

        result['builds'] = [{'id': row['id'], 'status': row['status'].name} for row in cursor.fetchall()]
        return result


def get_build(dbm, build_id):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            build.id,
            specification.spec_sha256,
            build.status,
            build.size,
            build.store_path,
            build.scheduled_on,
            build.started_on,
            build.ended_on
          FROM build
          INNER JOIN specification ON build.specification_id = specification.id
          WHERE build.id = ?
        ''', (build_id,))
        result = cursor.fetchone()

        cursor.execute('''
          SELECT
              conda_package.name,
              conda_package.version,
              conda_package.channel
          FROM conda_package
          INNER JOIN build_package ON conda_package.id = build_package.conda_package_id
          WHERE build_package.build_id = ?
        ''', (build_id,))
        result['packages'] = cursor.fetchall()
        result['status'] = result['status'].name
        return result


def get_build_log_key(dbm, build_id):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            specification.name,
            specification.spec_sha256,
            build.id
          FROM build
          INNER JOIN specification ON build.specification_id = specification.id
          WHERE build.id = ?
        ''', (build_id,))
        result = cursor.fetchone()
        return f'logs/{result["name"]}/{result["spec_sha256"]}/{result["id"]}.txt'


def get_build_archive_key(dbm, build_id):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            specification.name,
            specification.spec_sha256,
            build.id
          FROM build
          INNER JOIN specification ON build.specification_id = specification.id
          WHERE build.id = ?
        ''', (build_id,))
        result = cursor.fetchone()
        return f'archive/{result["name"]}/{result["spec_sha256"]}/{result["id"]}.tar.gz'


def get_build_lockfile(dbm, build_id):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            channel,
            subdir,
            name,
            version,
            build,
            md5
          FROM conda_package
          INNER JOIN build_package ON conda_package.id = build_package.conda_package_id
          WHERE build_package.build_id = ?
        ''', (build_id,))

    return '''#platform: linux-64
@EXPLICIT
{0}
'''.format('\n'.join(['{channel}/{subdir}/{name}-{version}-{build}.tar.bz2#{md5}'.format(**v) for v in cursor.fetchall()]))




def get_build_docker_archive(dbm, build_id):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            build.docker_path,
            specification.name,
            specification.spec_sha256
          FROM build
          INNER JOIN specification ON build.specification_id = specification.id
          WHERE build.id = ?
        ''', (build_id,))
        return cursor.fetchone()


def list_conda_packages(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            channel,
            build,
            build_number,
            constrains,
            depends,
            license,
            license_family,
            md5,
            name,
            sha256,
            size,
            subdir,
            timestamp,
            version
          FROM conda_package
          LIMIT 10
        ''')
    return cursor.fetchall()


def get_metrics(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            free_storage AS free,
            total_storage AS total,
            disk_usage,
            (SELECT COUNT(*) FROM build WHERE status = ?) AS total_completed_builds,
            (SELECT COUNT(*) FROM environment) AS total_environments
          FROM conda_store WHERE id = 1
        ''', (BuildStatus.COMPLETED,))
        #metrics1 = cursor.fetchone()
        metrics = {}
        metrics['total'] = 1
        metrics['used'] = 1
        metrics['percent'] = 1
        metrics['disk_usage'] = 0
        return metrics
