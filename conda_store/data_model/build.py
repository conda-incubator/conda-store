import logging
import datetime

from conda_store.data_model.base import BuildStatus
from conda_store.data_model.package import link_packages_to_build

logger = logging.getLogger(__name__)


def register_environment(dbm, environment):
    with dbm.transaction() as cursor:
        # only register new environment if specification does not already exist
        cursor.execute('SELECT COUNT(*) AS count FROM specification WHERE spec_sha256 = ?', (environment.spec_sha256,))
        if cursor.fetchone()['count'] == 0:
            logger.info(f'ensuring environment name={environment.name} filename={environment.filename} exists')
            cursor.execute('INSERT OR IGNORE INTO environment (name) VALUES (?)', (environment.name,))

            logger.info(f'registering environment name={environment.name} filename={environment.filename}')
            environment_row = (environment.name, environment.created_on, environment.filename, environment.spec, environment.spec_sha256)
            cursor.execute('INSERT INTO specification (name, created_on, filename, spec, spec_sha256) VALUES (?, ?, ?, ?, ?)', environment_row)

            logger.info(f'scheduling environment for build name={environment.name} filename={environment.filename}')
            environment_directory = dbm.store_directory / f'{environment.spec_sha256}-{environment.name}'
            cursor.execute('INSERT INTO build (specification_id, status, scheduled_on, store_path, archive_path) VALUES (?, ?, ?, ?, ?)',
                           (cursor.lastrowid, BuildStatus.QUEUED, datetime.datetime.now(), str(environment_directory), f'{environment_directory}.tar.gz'))
        else:
            logger.debug(f'environment name={environment.name} filename={environment.filename} already registered')


def number_queued_conda_builds(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('SELECT COUNT(*) AS count FROM build WHERE status = ?', (BuildStatus.QUEUED,))
        return cursor.fetchone()['count']


def number_schedulable_conda_builds(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('SELECT COUNT(*) AS count FROM build WHERE status = ? AND scheduled_on < ?', (BuildStatus.QUEUED, datetime.datetime.now()))
        return cursor.fetchone()['count']


def claim_conda_build(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
           SELECT
             build.id,
             specification.spec,
             build.store_path,
             build.archive_path
           FROM build INNER JOIN specification ON build.specification_id = specification.id
           WHERE status = ? AND scheduled_on < ? LIMIT 1
        ''', (BuildStatus.QUEUED, datetime.datetime.now()))
        result = cursor.fetchone()
        cursor.execute('UPDATE build SET status = ?, started_on = ? WHERE id = ?', (BuildStatus.BUILDING, datetime.datetime.now(), result['id']))
    return result['id'], result['spec'], result['store_path'], result['archive_path']


def update_conda_build_completed(dbm, build_id, logs, packages, size):
    logger.debug(f'build for build_id={build_id} completed')
    with dbm.transaction() as cursor:
        cursor.execute('UPDATE build SET status = ?, logs = ?, ended_on = ?, size = ? WHERE id = ?', (BuildStatus.COMPLETED, logs, datetime.datetime.now(), size, build_id))

        cursor.execute('''
          SELECT
            specification.name,
            specification.id
          FROM specification WHERE id = (SELECT specification_id FROM build WHERE id = ?)
        ''', (build_id,))
        result = cursor.fetchone()
        cursor.execute('''
           INSERT INTO environment (name, specification_id, build_id) VALUES (?, ?, ?)
             ON CONFLICT(name) DO UPDATE SET specification_id = ?, build_id = ?
        ''', (result['name'], result['id'], build_id, result['id'], build_id))

        link_packages_to_build(dbm, build_id, packages)


def update_conda_build_failed(dbm, build_id, logs, reschedule=True):
    logger.debug(f'build for build_id={build_id} failed')
    with dbm.transaction() as cursor:
        cursor.execute('UPDATE build SET status = ?, logs = ?, ended_on = ? WHERE id = ?', (BuildStatus.FAILED, logs, datetime.datetime.now(), build_id))

        if reschedule:
            cursor.execute('SELECT COUNT(*) AS count FROM build WHERE specification_id = (SELECT specification_id FROM build WHERE id = ?)', (build_id,))
            num_failed_builds = cursor.fetchone()['count']
            logger.info(f'environment build has failed={num_failed_builds} times')
            scheduled_on = datetime.datetime.now() + datetime.timedelta(seconds=10*(2**num_failed_builds))
            reschedule_failed_build(dbm, build_id, scheduled_on)


def reschedule_failed_build(dbm, build_id, scheduled_on):
    with dbm.transaction() as cursor:
        cursor.execute('''
          SELECT
            specification_id,
            store_path
          FROM build WHERE id = ?
        ''', (build_id,))
        result = cursor.fetchone()
        logger.info(f'rescheduling specification_id={result["specification_id"]} on {scheduled_on}')
        cursor.execute('INSERT INTO build (specification_id, status, scheduled_on, store_path) VALUES (?, ?, ?, ?)',
                       (result['specification_id'], BuildStatus.QUEUED, scheduled_on, result['store_path']))
