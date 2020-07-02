import logging

logger = logging.getLogger(__name__)

from conda_store.environments import parse_environment_spec
from conda_store.data_model.base import BuildStatus
from conda_store.data_model.build import register_environment


def list_environments(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT environment.name, environment.build_id, environment.specification_id, build.store_path, build.size
          FROM environment
          INNER JOIN specification ON environment.specification_id = specification.id
          INNER JOIN build ON environment.build_id = build.id
        ''')
        data = []
        for row in cursor.fetchall():
            data.append({
                'name': row[0],
                'build_id': row[1],
                'specification_id': row[2],
                'store_path': row[3],
                'size': row[4]
            })
        return data


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
    environment = parse_environment_spec(spec)
    register_environment(dbm, environment)


def get_specification(dbm, sha256):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT name, created_on, filename, spec, spec_sha256, (
             SELECT COUNT(*) FROM build
             INNER JOIN specification ON specification.id = build.specification_id
             WHERE specification.spec_sha256 = ?
          ) AS num_builds
          FROM specification
          WHERE spec_sha256 = ?
        ''', (sha256, sha256))
        name, created_on, filename, spec, spec_sha256, num_builds = cursor.fetchone()

        cursor.execute('''
          SELECT build.id
          FROM build
          INNER JOIN specification ON specification.id = build.specification_id
          WHERE specification.spec_sha256 = ?
        ''', (sha256,))
        builds = [_[0] for _ in cursor.fetchall()]

        return {
            'name': name,
            'created_on': created_on,
            'filename': filename,
            'spec': spec,
            'spec_sha256': spec_sha256,
            'builds': builds,
            'num_builds': num_builds,
        }


def get_build(dbm, build_id):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT specification_id, status, SUBSTR(logs, -256), size, store_path, scheduled_on, started_on, ended_on
          FROM build WHERE id = ?
        ''', (build_id,))
        specification_id, status, logs, size, store_path, scheduled_on, started_on, ended_on = cursor.fetchone()

        return {
            'specification_id': specification_id,
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
