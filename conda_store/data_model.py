import sqlite3
import enum


class BuildStatus(enum.Enum):
    QUEUED = 'QUEUED'
    BUILDING = 'BUILDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


SQL_TABLES = """
CREATE TABLE IF NOT EXISTS environment (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   sha256_hash TEXT,
   name TEXT,
   created TEXT,
   filename TEXT,
   spec TEXT,
   locked_spec TEXT
);

CREATE TABLE IF NOT EXISTS build (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment_id INTEGER,
  status TEXT,     # [enum]
  log BLOB,
  size INTEGER,    # [bytes]
  path TEXT,       # [path]
  created TEXT,    # [datetime]
  build_time REAL, # [seconds]
  FOREIGN KEY(environment_id) REFERENCES environment(id)
)
"""


class DatabaseManager:
    def __init__(self, store_directory):
        self.store_directory
        self.connection = self.create_database()
        self.create_tables()

    def create_database(self):
        connection = sqlite3.connect(str(store_directory / 'conda-store.sqlite'))
        return connection

    def create_tables(self):
        self.connection.execute(SQL_TABLES)
