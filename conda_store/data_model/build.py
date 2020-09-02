import logging
import datetime

from conda_store.data_model.base import BuildStatus

logger = logging.getLogger(__name__)


def register_environment(dbm, environment):
    with dbm.transaction() as cursor:
        # only register new environment if specification does not already exist
        cursor.execute('SELECT COUNT(*) FROM specification WHERE spec_sha256 = ?', (environment.spec_sha256,))
        if cursor.fetchone()[0] == 0:
            logger.info(f'ensuring environment name={environment.name} filename={environment.filename} exists')
            cursor.execute('INSERT OR IGNORE INTO environment (name) VALUES (?)', (environment.name,))

            logger.info(f'registering environment name={environment.name} filename={environment.filename}')
            environment_row = (environment.name, environment.created_on, environment.filename, environment.spec, environment.spec_sha256)
            cursor.execute('INSERT INTO specification (name, created_on, filename, spec, spec_sha256) VALUES (?, ?, ?, ?, ?)', environment_row)

            logger.info(f'scheduling environment for build name={environment.name} filename={environment.filename}')
            environment_directory = dbm.store_directory / f'{environment.spec_sha256}-{environment.name}'
            build_row = (cursor.lastrowid, BuildStatus.QUEUED, datetime.datetime.now(), str(environment_directory))
            cursor.execute('INSERT INTO build (specification_id, status, scheduled_on, store_path) VALUES (?, ?, ?, ?)', build_row)
        else:
            logger.debug(f'environment name={environment.name} filename={environment.filename} already registered')


def number_queued_conda_builds(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('SELECT COUNT(*) FROM build WHERE status = ?', (BuildStatus.QUEUED,))
        return cursor.fetchone()[0]


def number_schedulable_conda_builds(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('SELECT COUNT(*) FROM build WHERE status = ? AND scheduled_on < ?', (BuildStatus.QUEUED, datetime.datetime.now()))
        return cursor.fetchone()[0]


def claim_conda_build(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('''
           SELECT build.id, specification.spec, build.store_path
           FROM build INNER JOIN specification ON build.specification_id = specification.id
           WHERE status = ? AND scheduled_on < ? LIMIT 1
        ''', (BuildStatus.QUEUED, datetime.datetime.now()))
        build_id, spec, store_path = cursor.fetchone()
        cursor.execute('UPDATE build SET status = ?, started_on = ? WHERE id = ?', (BuildStatus.BUILDING, datetime.datetime.now(), build_id))
    return build_id, spec, store_path


def update_conda_build_completed(dbm, build_id, logs, packages, size):
    logger.debug(f'build for build_id={build_id} completed')
    with dbm.transaction() as cursor:
        cursor.execute('UPDATE build SET status = ?, logs = ?, ended_on = ?, size = ?, packages = ? WHERE id = ?', (BuildStatus.COMPLETED, logs, datetime.datetime.now(), size, packages, build_id))

        cursor.execute('SELECT name, id FROM specification WHERE id = (SELECT specification_id FROM build WHERE id = ?)', (build_id,))
        name, specification_id = cursor.fetchone()
        cursor.execute('''
           INSERT INTO environment (name, specification_id, build_id) VALUES (?, ?, ?)
             ON CONFLICT(name) DO UPDATE SET specification_id = ?, build_id = ?
        ''', (name, specification_id, build_id, specification_id, build_id))


def update_conda_build_failed(dbm, build_id, logs, reschedule=True):
    logger.debug(f'build for build_id={build_id} failed')
    with dbm.transaction() as cursor:
        cursor.execute('UPDATE build SET status = ?, logs = ?, ended_on = ? WHERE id = ?', (BuildStatus.FAILED, logs, datetime.datetime.now(), build_id))

        if reschedule:
            cursor.execute('SELECT COUNT(*) FROM build WHERE specification_id = (SELECT specification_id FROM build WHERE id = ?)', (build_id,))
            num_failed_builds = cursor.fetchone()[0]
            logger.info(f'environment build has failed={num_failed_builds} times')
            scheduled_on = datetime.datetime.now() + datetime.timedelta(seconds=10*(2**num_failed_builds))
            reschedule_failed_build(dbm, build_id, scheduled_on)


def reschedule_failed_build(dbm, build_id, scheduled_on):
    with dbm.transaction() as cursor:
        cursor.execute('SELECT specification_id, store_path FROM build WHERE id = ?', (build_id,))
        specification_id, store_path = cursor.fetchone()
        logger.info(f'rescheduling specification_id={specification_id} on {scheduled_on}')
        build_row = (specification_id, BuildStatus.QUEUED, scheduled_on, store_path)
        cursor.execute('INSERT INTO build (specification_id, status, scheduled_on, store_path) VALUES (?, ?, ?, ?)', build_row)
