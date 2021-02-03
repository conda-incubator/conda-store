import sqlite3
import enum
import datetime
import logging
import json
import dataclasses
import contextlib

from sqlalchemy import (
    Column, Integer, String, ForeignKey, JSON, Enum, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine


logger = logging.getLogger(__name__)


Base = declarative_base()


class BuildStatus(enum.Enum):
    QUEUED = enum.auto()
    BUILDING = enum.auto()
    COMPLETED = enum.auto()
    FAILED = enum.auto()


class Environment(Base):
    __tablename__ = 'environment'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    specification_id = Column(Integer, ForeignKey("specification.id"))
    specification = relationship(
        Specification,
        backref=backref('specification', uselist=False),
        single_parent=True,
        cascade="all, delete-orphan",
    )

    build_id = Column(Integer, ForeignKey("build.id"))
    build = relationship(
        Build,
        backref=backref('build', uselist=False),
        single_parent=True,
        cascade="all, delete-orphan",
    )


class Specification(Base):
    __tablename__ = 'specification'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_on = Column(DateTime, default=datetime.datetime.utcnow)
    filename = Column(String)
    spec = Column(JSON)
    spec_sha256 = Column(String, unique=True)


class Build(Base):
    __tablename__ = 'build'

    id = Column(Integer, primary_key=True)
    specification_id = Column(Integer, ForeignKey("specification.id"))
    specification = relationship(
        Specification,
        backref=backref('specification', uselist=False),
        single_parent=True,
        cascade="all, delete-orphan",
    )

    status = Column(Enum(BuildStatus))
    size = Column(Integer)
    packages = Column(JSON)
    store_path = Column(String)
    scheduled_on = Column(DateTime)
    started_on = Column(DateTime)
    ended_on = Column(DateTime)


class BuildPackage(Base):
    __tablename__ = 'build_package'

    build_id = Column(Integer, primary_key=True, ForeignKey("build.id"))
    conda_package_id = Column(Integer, primary_key=True, ForeignKey("conda_package.id"))


class CondaPackage(Base):
    __tablename__ = 'conda_package'

    id = Column(Integer, primary_key=True)
    channel = Column(String)
    build = Column(String)
    build_number = Column(Integer)
    constrains = Column(JSON)
    depends = Column(JSON)
    license = Column(String)
    license_family = Column(String)
    md5 = Column(String)
    name = Column(String)
    sha256 = Column(String, unique=True)
    size = Column(Integer)
    subdir = Column(String)
    timestamp = Column(Integer)
    version = Column(String)


class CondaStore(Base):
    __tablename__ = 'conda_store'

    id = Column(Integer, primary_key=True)
    last_package_update = Column(DateTime)
    free_storage = Column(Integer)
    total_storage = Column(Integer)


def new_session_factory(url="sqlite:///:memory:", reset=False, **kwargs):
    engine = create_engine(url, **kwargs)

    if reset:
        Base.metadata.drop_all(engine)

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine)
    return session_factory


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
