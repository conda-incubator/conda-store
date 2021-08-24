from typing import List

from sqlalchemy import func

from conda_store_server import orm
from .conda import conda_platform


def list_namespaces(db):
    filters = []
    return db.query(orm.Namespace).filter(*filters)


def get_namespace(db, name: str = None, id: int = None):
    filters = []
    if name:
        filters.append(orm.Namespace.name == name)
    if id:
        filters.append(orm.Namespace.id == id)
    return db.query(orm.Namespace).filter(*filters).first()


def list_environments(db, namespace: str = None, search=None):
    filters = []
    if namespace:
        filters.append(orm.Namespace.name == namespace)

    return db.query(orm.Environment).join(orm.Environment.namespace).filter(*filters)


def get_environment(
    db,
    name: str = None,
    namespace: str = None,
    namespace_id: int = None,
    id: int = None,
):
    filters = []
    if namespace:
        filters.append(orm.Namespace.name == namespace)
    if namespace_id:
        filters.append(orm.Namespace.id == namespace_id)
    if name:
        filters.append(orm.Environment.name == name)
    if id:
        filters.append(orm.Environment.id == id)

    return db.query(orm.Environment).join(orm.Namespace).filter(*filters).first()


def get_environment_builds(db, namespace, name):
    return (
        db.query(orm.Build)
        .join(orm.Specification, orm.Build.specification_id == orm.Specification.id)
        .join(orm.Namespace, orm.Build.namespace_id == orm.Namespace.id)
        .filter(orm.Namespace.name == namespace, orm.Specification.name == name)
        .all()
    )


def list_specifications(db, search=None):
    return db.query(orm.Specification).all()


def get_specification(db, sha256):
    return (
        db.query(orm.Specification).filter(orm.Specification.sha256 == sha256).first()
    )


def post_specification(conda_store, specification, namespace=None):
    conda_store.register_environment(specification, namespace)


def list_builds(db, status: orm.BuildStatus = None):
    filters = []
    if status:
        filters.append(orm.Build.status == status)

    return db.query(orm.Build).filter(*filters)


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


def get_build_artifact_types(db, build_id):
    return (
        db.query(orm.BuildArtifact.artifact_type)
        .filter(orm.BuildArtifact.build_id == build_id)
        .distinct()
    )


def list_build_artifacts(
    db,
    limit: int = 25,
    build_id: int = None,
    key: str = None,
    excluded_artifact_types: List[orm.BuildArtifactType] = None,
):
    filters = []
    if build_id:
        filters.append(orm.BuildArtifact.build_id == build_id)
    if key:
        filters.append(orm.BuildArtifact.key == key)
    if excluded_artifact_types:
        filters.append(
            func.not_(orm.BuildArtifact.artifact_type.in_(excluded_artifact_types))
        )

    return db.query(orm.BuildArtifact).filter(*filters).limit(limit).all()


def get_build_artifact(db, build_id, key):
    return (
        db.query(orm.BuildArtifact)
        .filter(orm.BuildArtifact.build_id == build_id, orm.BuildArtifact.key == key)
        .first()
    )


def list_conda_channels(db, limit=25):
    return db.query(orm.CondaChannel).limit(limit).all()


def get_conda_channel(db, channel_name):
    return (
        db.query(orm.CondaChannel).filter(orm.CondaChannel.name == channel_name).first()
    )


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
