import datetime

from traitlets import Integer

from conda_store_server import orm, schema, api
from conda_store_server.build.base import CondaStoreBuilder


class SolveBuilder(CondaStoreBuilder):
    build_artifacts = [
        "LOCKFILE",
    ]

    depends_on = []

    conda_max_solve_time = Integer(
        5 * 60,  # 5 minute
        help="Maximum time in seconds to allow for solving a given conda environment",
        config=True,
    )

    def build_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        build = api.get_build(conda_store.db, build_id)
        if artifact_type == "LOCKFILE":
            solve_conda_environment(conda_store, solve)

    def delete_artifact(self, conda_store: "CondaStore", artifact_type: str, build_id: str):
        for build_artifact in api.list_build_artifacts(
                db=conda_store.db,
                build_id=build_id,
                included_artifact_types=[artifact_type]
        ):
            conda_store.storage.delete(
                conda_store.db, build_artifact.build.id, build_artifact.key
            )


def solve_conda_environment(conda_store, solve):
    from conda_store_server.conda import conda_lock

    try:
        solve.started_on = datetime.datetime.utcnow()
        conda_store.db.commit()

        specification = schema.CondaSpecification.parse_obj(solve.specification.spec)
        packages = conda_lock(specification, conda_store.conda_command)

        for package in packages["conda"]:
            channel = package["channel_id"]
            if channel == "https://conda.anaconda.org/pypi":
                # ignore pypi package for now
                continue

            channel_orm = api.get_conda_channel(conda_store.db, channel)
            if channel_orm is None:
                if len(conda_store.conda_allowed_channels) == 0:
                    channel_orm = api.create_conda_channel(conda_store.db, channel)
                    conda_store.db.commit()
                else:
                    raise ValueError(
                        f"channel url={channel} not recognized in conda-store channel database"
                    )
            package["channel_id"] = channel_orm.id

            _package = (
                conda_store.db.query(orm.CondaPackage)
                .filter(orm.CondaPackage.md5 == package["md5"])
                .filter(orm.CondaPackage.channel_id == package["channel_id"])
                .first()
            )

            if _package is None:
                _package = orm.CondaPackage(**package)
                conda_store.db.add(_package)
            solve.packages.append(_package)
        solve.ended_on = datetime.datetime.utcnow()
        conda_store.db.commit()
    except Exception as e:
        print("Task failed!!!!!!!!!!!", str(e))
        raise e
