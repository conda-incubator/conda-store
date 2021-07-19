import datetime

from sqlalchemy import and_, func

from conda_store_server import orm
from .conda import conda_platform


def list_environments(db, namespace : str=None, search=None):
    filters = []
    if namespace:
        filters.append(orm.Environment.namespace == namespace)

    return db.query(orm.Environment).filter(*filters).all()


def get_environment(db, name, namespace : str=None):
    filters = [orm.Environment.name == name]

    if namespace:
        filters.append(orm.Environment.namespace == namespace)

    return db.query(orm.Environment).filter(*filters).first()


def get_environment_builds(db, name):
    return (
        db.query(orm.Build)
        .join(orm.Specification, orm.Build.specification_id == orm.Specification.id)
        .filter(orm.Specification.name == name)
        .all()
    )


def list_specifications(db, search=None):
    return db.query(orm.Specification).all()


def get_specification(db, sha256):
    return (
        db.query(orm.Specification).filter(orm.Specification.sha256 == sha256).first()
    )


def post_specification(conda_store, specification, namespace="library"):
    conda_store.register_environment(specification, namespace="library")


def list_builds(db, limit : int=25, status : orm.BuildStatus=None):
    filters = []
    if status:
        filters.append(orm.Build.status == status)

    return db.query(orm.Build).filter(*filters).limit(limit).all()


def get_build(db, build_id):
    return db.query(orm.Build).filter(orm.Build.id == build_id).first()


def get_num_queued_builds(db, status):
    return (
        db.query(orm.Build).filter(orm.Build.status == orm.BuildStatus.QUEUED).count()
    )



def get_build_lockfile(db, build_id):
    build = db.query(orm.Build).filter(orm.Build.id == build_id).first()
    packages = [
        f"{row.channel.name}/{row.subdir}/{row.name}-{row.version}-{row.build}.tar.bz2#{row.md5}"
        for row in build.packages
    ]
    return """#platform: {0}
@EXPLICIT
{1}
""".format(
        conda_platform(), "\n".join(packages)
    )


def list_conda_channels(db, limit=25):
    return db.query(orm.CondaChannel).limit(limit).all()


def get_conda_channel(db, channel_name):
    return db.query(orm.CondaChannel).filter(orm.CondaChannel.name == channel_name).first()


def list_conda_packages(db, limit=25):
    return db.query(orm.CondaPackage).limit(limit).all()


def get_metrics(db):
    metrics = (
        db.query(
            orm.CondaStoreConfiguration.free_storage.label("disk_free"),
            orm.CondaStoreConfiguration.total_storage.label("disk_total"),
            orm.CondaStoreConfiguration.disk_usage,
        )
        .first()
        ._asdict()
    )

    query = db.query(func.count(orm.Build.status), orm.Build.status).group_by(
        orm.Build.status
    )
    for build_count, build_status_enum in query.all():
        metrics[f"build_{build_status_enum.value.lower()}"] = build_count

    metrics["environments"] = db.query(orm.Environment).count()
    return metrics
