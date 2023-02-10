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
    assert len(build.package_builds) == 2

    # now query directly
    m2ms = db_session.query(
        orm.build_conda_package
    ).filter(
        orm.build_conda_package.columns.build_id == build_id
    ).all()
    assert len(m2ms) == 2


def test_get_build_lockfile(mocker, db_session):
    mocker.patch(
        "conda_store_server.api.conda_platform",
        return_value="linux-64",
    )

    response_text = api.get_build_lockfile(db_session, 1)

    for indx, line in enumerate(response_text.split("\n")):
        if indx == 0:
            assert line == "# platform: linux-64"
            continue

        if indx == 1:
            assert line == "@EXPLICIT"
            continue

        if indx == 2:
            assert "https://conda.anaconda.org/conda-forge/linux-64/icu-70.1-h27087fc_0.conda#87473a15119779e021c314249d4b4aed"

        if indx == 3:
            assert "https://conda.anaconda.org/conda-forge/linux-64/zarr-2.12.0-pyhd8ed1ab_0.tar.bz2#37d4251d34eb991ff9e40e546cc2e803"