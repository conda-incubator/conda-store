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
    size: int
    packages: list
    store_path: str
    created_on: datetime.datetime
    build_on: datetime.datetime
    build_time: float


@dataclasses.dataclass
class CondaPackage:
    channel: str
    build: str
    build_number: int
    constrains: list
    depends: list
    license: str
    license_family: str
    md5: str
    name: str
    sha256: str
    size: int
    subdir: str
    timestamp: int
    version: str


SQL_TABLES = """
CREATE TABLE IF NOT EXISTS conda_store (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  last_package_update DATETIME,
  free_storage INTEGER,
  total_storage INTEGER,
  disk_usage INTEGER
);

CREATE TABLE IF NOT EXISTS conda_package (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  channel TEXT,
  build TEXT,
  build_number INTEGER,
  constrains JSON,
  depends JSON,
  license TEXT,
  license_family TEXT,
  md5 TEXT,
  name TEXT,
  sha256 TEXT,
  size INTEGER,
  subdir TEXT,
  timestamp INTEGER,
  version TEXT,
  UNIQUE(sha256)
);

CREATE TABLE IF NOT EXISTS build_package (
  build_id INTEGER,
  conda_package_id INTEGER,
  PRIMARY KEY(build_id, conda_package_id),
  FOREIGN KEY(build_id) REFERENCES build(id),
  FOREIGN KEY(conda_package_id) REFERENCES conda_package(id)
);

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
  size INTEGER,
  packages JSON,
  store_path TEXT,
  scheduled_on DATETIME,
  started_on DATETIME,
  ended_on DATETIME,
  FOREIGN KEY(specification_id) REFERENCES specification(id)
)
"""


def dict_factory(cursor, row):
    d = {}
    for index, column in enumerate(cursor.description):
        d[column[0]] = row[index]
    return d


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
            return BuildStatus(int(value))

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
        connection.row_factory = dict_factory

        return connection

    def create_tables(self):
        with self.transaction() as cursor:
            cursor.executescript(SQL_TABLES)

    @contextlib.contextmanager
    def transaction(self):
        with self.connection:
            cursor = self.connection.cursor()
            yield cursor
