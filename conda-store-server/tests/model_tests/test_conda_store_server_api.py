from conda_store_server import orm, schema, api


def test_conftest_relationship_lookups(db_session):
    build_id = 1

    build = db_session.query(orm.Build).filter_by(id=build_id).first()
    assert build.status == schema.BuildStatus.COMPLETED

    build_artifact = db_session.query(orm.BuildArtifact).filter_by(id=build_id).first()
    assert build_artifact.artifact_type == schema.BuildArtifactType.LOCKFILE

    #############################################
    # test relationship resolutions
    #############################################
    assert build.build_artifacts[0].id == build_artifact.id

    # make sure the relationship resolves through the secondary
    assert len(build.package_builds) == 3

    # now query directly
    m2ms = db_session.query(
        orm.build_conda_package
    ).filter(
        orm.build_conda_package.columns.build_id == build_id
    ).all()
    assert len(m2ms) == 3


def test_get_build_lockfile_for_tarball_ext(mocker, db_session):
    # https://github.com/Quansight/conda-store/issues/431
    build_id = 1
    mocker.patch(
        "conda_store_server.api.conda_platform",
        return_value="linux-64",
    )
    build = db_session.query(orm.Build).filter(orm.Build.id == build_id).first()
    conda_package_builds = build.package_builds
    lines = api.get_build_lockfile(db_session, build_id).split("\n")
    assert lines[0] == "# platform: linux-64"
    assert lines[1] == "@EXPLICIT"
    for conda_package_build_record, lockfile_line in zip(conda_package_builds, lines[2:]):
        if conda_package_build_record.tarball_ext:
            assert conda_package_build_record.tarball_ext in lockfile_line
        else:
            assert ".tar.bz2" in lockfile_line
