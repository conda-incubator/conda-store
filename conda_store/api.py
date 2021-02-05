import logging
import math
import datetime

from sqlalchemy import and_

from conda_store import orm

logger = logging.getLogger(__name__)


def get_num_queued_builds(db):
    return db.query(orm.Build).filter(
        orm.Build.status == orm.BuildStatus.QUEUED
    ).count()


def get_num_schedulable_builds(db):
    return db.query(orm.Build).filter(and_(
        orm.Build.status == orm.BuildStatus.QUEUED,
        orm.Build.scheduled_on < datetime.datetime.utcnow()
    )).count()


def get_build_lockfile(db, build_id):
    query = db.query(
        orm.CondaPackage.channel,
        orm.CondaPackage.subdir,
        orm.CondaPackage.name,
        orm.CondaPackage.version,
        orm.CondaPackage.build,
        orm.CondaPackage.md5
    ).join(
        orm.BuildCondaPackage, orm.CondaPackage.id == orm.BuildCondaPackage.conda_package_id
    ).filter(
        orm.BuildCondaPackage.build_id == build_id).all()
    packages = [f'{row.channel}/{row.subdir}/{row.name}-{row.version}-{row.build}.tar.bz2#{row.md5}' for row in query.all()]
    return '''#platform: linux-64
@EXPLICIT
{0}
'''.format('\n'.join(packages))


def get_build_docker_archive(db, storage, build_id):
    pass


def list_conda_packages(db, limit=10):
    query = db.query(
        orm.CondaPackage.channel,
        orm.CondaPackage.build,
        orm.CondaPackage.build_number,
        orm.CondaPackage.constrains,
        orm.CondaPackage.depends,
        orm.CondaPackage.license,
        orm.CondaPackage.license_family,
        orm.CondaPackage.md5,
        orm.CondaPackage.name,
        orm.CondaPackage.sha256,
        orm.CondaPackage.size,
        orm.CondaPackage.subdir,
        orm.CondaPackage.timestamp,
        orm.CondaPackage.version).limit(limit)
    return [row._asdict() for row in query.all()]


def get_metrics(db):
    metrics = db.query(
        orm.CondaStoreConfiguration.free_storage.label('free'),
        orm.CondaStoreConfiguration.total_storage.label('total'),
        orm.CondaStoreConfiguration.disk_usage).first()._asdict()

    metrics['total_completed_builds'] = db.query(orm.Build).filter(
        orm.Build.status == orm.BuildStatus.COMPLETED).count()
    metrics['total_environments'] = db.query(orm.Environment).count()
    metrics['used'] = metrics['total'] - metrics['free']
    metrics['percent'] = math.ceil(metrics['used'] / metrics['total'] * 100)
    return metrics
