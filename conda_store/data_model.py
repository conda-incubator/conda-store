import sqlite3
import enum
import datetime
import logging
import json
import dataclasses
import contextlib

logger = logging.getLogger(__name__)


class BuildStatus(enum.Enum):
    QUEUED = enum.auto()
    BUILDING = enum.auto()
    COMPLETED = enum.auto()
    FAILED = enum.auto()


@dataclasses.dataclass
class Environment:
    name: str
    created_on: datetime.datetime
    filename: str
    spec: dict
    spec_sha256: bytes


@dataclasses.dataclass
class Build:
    environment_id: int
    status: int
    logs: bytes
    size: int
    path: str
    created_on: datetime.datetime
    build_on: datetime.datetime
    build_time: float


SQL_TABLES = """
CREATE TABLE IF NOT EXISTS environment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  specification_id INTEGER,
  build_id INTEGER,
  UNIQUE(name),
  FOREIGN KEY(specification_id) REFERENCES specification(id)
  FOREIGN KEY(build_id) REFERENCES build(id)
);

CREATE TABLE IF NOT EXISTS specification (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   name TEXT,
   created_on DATETIME,
   filename TEXT,
   spec JSON,
   spec_sha256 BLOB,
   UNIQUE(spec_sha256)
);

CREATE TABLE IF NOT EXISTS build (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  specification_id INTEGER,
  status ENUM,
  logs TEXT,
  size INTEGER,
  store_path TEXT,
  install_path TEXT,
  scheduled_on DATETIME,
  started_on DATETIME,
  ended_on DATETIME,
  FOREIGN KEY(specification_id) REFERENCES specification(id)
)
"""


class DatabaseManager:
    def __init__(self, store_directory):
        self.store_directory = store_directory
        self.connection = self.create_database()
        self.create_tables()

    def close(self):
        self.connection.close()

    def create_database(self):
        def adapt_datetime(datetime):
            return (datetime.strftime('%Y-%m-%d %H:%M:%S.%f')).encode()

        def convert_datetime(blob):
            return datetime.datetime.strptime(blob.decode(), '%Y-%m-%d %H:%M:%S.%f')

        def adapt_json(data):
            return (json.dumps(data, sort_keys=False)).encode()

        def convert_json(blob):
            return json.loads(blob.decode())

        def adapt_enum(enum):
            return enum.value

        def convert_enum(value):
            return BuildStatus(value)

        sqlite3.register_adapter(datetime.datetime, adapt_datetime)
        sqlite3.register_adapter(datetime.date, adapt_datetime)
        sqlite3.register_adapter(dict, adapt_json)
        sqlite3.register_adapter(list, adapt_json)
        sqlite3.register_adapter(tuple, adapt_json)
        sqlite3.register_adapter(BuildStatus, adapt_enum)

        sqlite3.register_converter('DATETIME', convert_datetime)
        sqlite3.register_converter('JSON', convert_json)
        sqlite3.register_converter('ENUM', convert_enum)

        connection = sqlite3.connect(str(self.store_directory / 'conda-store.sqlite'), detect_types=sqlite3.PARSE_DECLTYPES)
        return connection

    def create_tables(self):
        with self.transaction() as cursor:
            cursor.executescript(SQL_TABLES)

    @contextlib.contextmanager
    def transaction(self):
        with self.connection:
            cursor = self.connection.cursor()
            yield cursor


# ========== CONDA BUILD API ============
def register_environment(dbm, environment, install_directory):
    with dbm.transaction() as cursor:
        # only register new environment if it does not already exist
        cursor.execute('SELECT COUNT(*) FROM specification WHERE spec_sha256 = ?', (environment.spec_sha256,))
        if cursor.fetchone()[0] == 0:
            logger.info(f'registering environment name={environment.name} filename={environment.filename}')
            environment_row = (environment.name, environment.created_on, environment.filename, environment.spec, environment.spec_sha256)
            cursor.execute('INSERT INTO specification (name, created_on, filename, spec, spec_sha256) VALUES (?, ?, ?, ?, ?)', environment_row)

            logger.info(f'scheduling environment for build name={environment.name} filename={environment.filename}')
            environment_directory = dbm.store_directory / f'{environment.spec_sha256}-{environment.name}'
            environment_install_directory = install_directory / environment.name
            build_row = (cursor.lastrowid, BuildStatus.QUEUED, datetime.datetime.now(), str(environment_directory), str(environment_install_directory))
            cursor.execute('INSERT INTO build (specification_id, status, scheduled_on, store_path, install_path) VALUES (?, ?, ?, ?, ?)', build_row)
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
           SELECT build.id, specification.spec, build.store_path, build.install_path
           FROM build INNER JOIN specification ON build.specification_id = specification.id
           WHERE status = ? AND scheduled_on < ? LIMIT 1
        ''', (BuildStatus.QUEUED, datetime.datetime.now()))
        build_id, spec, store_path, install_path = cursor.fetchone()
        cursor.execute('UPDATE build SET status = ?, started_on = ? WHERE id = ?', (BuildStatus.BUILDING, datetime.datetime.now(), build_id))
    return build_id, spec, store_path, install_path


def update_conda_build_completed(dbm, build_id, logs, size):
    logger.debug(f'build for build_id={build_id} completed')
    with dbm.transaction() as cursor:
        cursor.execute('UPDATE build SET status = ?, logs = ?, ended_on = ?, size = ? WHERE id = ?', (BuildStatus.COMPLETED, logs, datetime.datetime.now(), size, build_id))

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
        cursor.execute('SELECT specification_id, store_path, install_path FROM build WHERE id = ?', (build_id,))
        specification_id, store_path, install_path = cursor.fetchone()
        logger.info(f'rescheduling specification_id={specification_id} on {scheduled_on}')
        build_row = (specification_id, BuildStatus.QUEUED, scheduled_on, store_path, install_path)
        cursor.execute('INSERT INTO build (specification_id, status, scheduled_on, store_path, install_path) VALUES (?, ?, ?, ?, ?)', build_row)


# ================ UI API =================
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
