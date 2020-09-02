import logging

logger = logging.getLogger(__name__)

from conda_store.environments import parse_environment_spec, validate_environment
from conda_store.data_model.base import BuildStatus
from conda_store.data_model.build import register_environment


def list_environments(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT environment.name, specification.spec_sha256, environment.build_id, build.store_path, build.size
          FROM environment
          LEFT JOIN specification ON environment.specification_id = specification.id
          LEFT JOIN build ON environment.build_id = build.id
          ORDER BY environment.name
        ''')
        data = []
        for row in cursor.fetchall():
            data.append({
                'name': row[0],
                'spec_sha256': row[1],
                'build_id': row[2],
                'store_path': row[3],
                'size': row[4]
            })
        return data


def get_environment(dbm, environment_name):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT environment.name, specification.spec_sha256, environment.build_id, build.store_path, build.size
          FROM environment
          LEFT JOIN specification ON environment.specification_id = specification.id
          LEFT JOIN build ON environment.build_id = build.id
          WHERE environment.name = ?
        ''', (environment_name,))
        result = cursor.fetchone()

        cursor.execute('''
          SELECT build.id, build.status
          FROM environment
          INNER JOIN specification ON environment.name = specification.name
          INNER JOIN build ON specification.id = build.specification_id
          WHERE environment.name = ?
        ''', (environment_name,))
        builds = [{'id': _[0], 'status': _[1].name} for _ in cursor.fetchall()]

        return {
            'name': result[0],
            'spec_sha256': result[1],
            'build_id': result[2],
            'store_path': result[3],
            'size': result[4],
            'builds': builds
        }


def list_specifications(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT name, created_on, filename, spec, spec_sha256
          FROM specification
        ''')
        data = []
        for row in cursor.fetchall():
            data.append({
                'name': row[0],
                'created_on': row[1],
                'filename': row[2],
                'spec': row[3],
                'spec_sha256': row[4],
            })
        return data


def post_specification(dbm, spec):
    if not validate_environment(spec):
        raise ValueError('Specification is not a valid conda environment')
    environment = parse_environment_spec(spec)
    register_environment(dbm, environment)


def get_specification(dbm, spec_sha256):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT specification.name, specification.created_on, specification.filename, specification.spec, (
             SELECT COUNT(*)
             FROM build
             INNER JOIN specification ON build.specification_id = specification.id
             WHERE specification.spec_sha256 = ?
          ) AS num_builds
          FROM specification
          WHERE specification.spec_sha256 = ?
        ''', (spec_sha256, spec_sha256))
        name, created_on, filename, spec, num_builds = cursor.fetchone()

        cursor.execute('''
          SELECT build.id, build.status
          FROM build
          INNER JOIN specification ON build.specification_id = specification.id
          WHERE specification.spec_sha256 = ?
        ''', (spec_sha256,))
        builds = [{'id': _[0], 'status': _[1].name} for _ in cursor.fetchall()]

        return {
            'name': name,
            'created_on': created_on,
            'filename': filename,
            'spec': spec,
            'spec_sha256': spec_sha256,
            'num_builds': num_builds,
            'builds': builds,
        }


def get_build(dbm, build_id):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT specification.spec_sha256, build.status, SUBSTR(build.logs, -256), build.size, build.store_path, build.scheduled_on, build.started_on, build.ended_on
          FROM build
          INNER JOIN specification ON build.specification_id = specification.id
          WHERE build.id = ?
        ''', (build_id,))
        spec_sha256, status, logs, size, store_path, scheduled_on, started_on, ended_on = cursor.fetchone()

        return {
            'id': build_id,
            'spec_sha256': spec_sha256,
            'status': status.name,
            'logs': logs,
            'size': size,
            'store_path': store_path,
            'scheduled_on': scheduled_on,
            'started_on': started_on,
            'ended_on': ended_on
        }


def get_build_logs(dbm, build_id):
    with dbm.transaction() as cursor:
        cursor.execute('SELECT logs FROM build WHERE id = ?', (build_id,))
    return cursor.fetchone()[0]
