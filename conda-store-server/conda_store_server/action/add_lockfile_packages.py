import typing

from conda.models.dist import Dist
from conda_store_server import action, api, conda_utils


def list_lockfile_packages(conda_lock_spec: typing.Dict):
    conda_packages = []
    platform = conda_utils.conda_platform()

    for package in conda_lock_spec["package"]:
        if package["manager"] == "conda" and package["platform"] == platform:
            dist = Dist.from_string(package["url"])
            conda_packages.append(
                {
                    "name": dist.name,
                    "build": dist.build,
                    "build_number": dist.build_number,
                    "constrains": None,
                    "depends": [],
                    "license": None,
                    "license_family": None,
                    "size": -1,
                    "subdir": dist.subdir,
                    "timestamp": None,
                    "version": dist.version,
                    "channel_id": dist.base_url,
                    "md5": package["hash"].get("md5"),
                    "sha256": package["hash"].get("sha256", ""),
                    "summary": None,
                    "description": None,
                }
            )
    return conda_packages


@action.action
def action_add_lockfile_packages(
    context, db, conda_lock_spec: typing.Dict, solve_id: int
):
    solve = api.get_solve(db, solve_id=solve_id)
    packages = list_lockfile_packages(conda_lock_spec)

    for package in packages:
        conda_package_build = api.create_or_ignore_conda_package(db, package)
        if conda_package_build is None:
            continue  # pypi package
        solve.package_builds.append(conda_package_build)
        db.commit()
