import pathlib
import os
import hashlib
import json

from conda.core.prefix_data import PrefixData

from conda_store_server import action, orm, api


def list_conda_prefix_packages(conda_prefix: pathlib.Path):
    """
    Returns a list of the packages that exist for a given prefix

    """
    packages = []

    prefix_data = PrefixData(str(conda_prefix))
    prefix_data.load()

    for record in prefix_data.iter_records():
        package = {
            "build": record.build,
            "build_number": record.build_number,
            "constrains": list(record.constrains),
            "depends": list(record.depends),
            "license": record.license,
            "license_family": record.license_family,
            "md5": hashlib.md5(
                open(record.package_tarball_full_path, "rb").read()
            ).hexdigest(),
            "sha256": hashlib.sha256(
                open(record.package_tarball_full_path, "rb").read()
            ).hexdigest(),
            "name": record.name,
            "size": getattr(record, "size", None),
            "subdir": record.subdir,
            "timestamp": record.timestamp,
            "version": record.version,
            "channel_id": record.channel.base_url,
            "summary": None,
            "description": None,
        }

        info_json = os.path.join(record.extracted_package_dir, "info/about.json")
        if os.path.exists(info_json):
            info = json.load(open(info_json))
            package["summary"] = info.get("summary")
            package["description"] = info.get("description")

        packages.append(package)
    return packages


@action.action
def action_add_conda_prefix_packages(
    context,
    db,
    conda_prefix: pathlib.Path,
    build_id: int,
):
    build = api.get_build(db, build_id=build_id)
    packages = list_conda_prefix_packages(conda_prefix)

    package_keys = [
        "channel_id",
        "license",
        "license_family",
        "name",
        "version",
        "summary",
        "description",
    ]
    package_build_keys = [
        "build",
        "build_number",
        "constrains",
        "depends",
        "md5",
        "sha256",
        "size",
        "subdir",
        "timestamp",
    ]

    for package in packages:
        channel = package["channel_id"]
        if channel == "https://conda.anaconda.org/pypi":
            # ignore pypi package for now
            continue

        channel_orm = api.get_conda_channel(db, channel)
        if channel_orm is None:
            channel_orm = api.create_conda_channel(db, channel)
            db.commit()

        package["channel_id"] = channel_orm.id

        # Retrieve the package from the DB if it already exists
        _package = (
            db.query(orm.CondaPackage)
            .filter(orm.CondaPackage.channel_id == package["channel_id"])
            .filter(orm.CondaPackage.name == package["name"])
            .filter(orm.CondaPackage.version == package["version"])
            .first()
        )

        # If it doesn't exist, let's create it in DB
        if _package is None:
            package_dict = {k: package[k] for k in package_keys}
            _package = orm.CondaPackage(**package_dict)
            db.add(_package)

        # Retrieve the build for this pacakge, if it already exists
        _package_build = (
            db.query(orm.CondaPackageBuild)
            .filter(orm.CondaPackageBuild.package == _package)
            .filter(orm.CondaPackageBuild.md5 == package["md5"])
            .first()
        )

        # If it doesn't exist, let's create it in DB
        if _package_build is None:
            package_build_dict = {k: package[k] for k in package_build_keys}
            # Attach the package_build to its package
            package_build_dict["package_id"] = _package.id
            _package_build = orm.CondaPackageBuild(**package_build_dict)
            db.add(_package_build)

        build.package_builds.append(_package_build)
        db.commit()
