from conda_store_server import orm, schema, api


def test_mocked_toolchain_example(mocked_session):
    # an example making sure the mocking toolchain works
    build = mocked_session.query(orm.Build).filter_by(id=1).first()
    assert build.status == schema.BuildStatus.COMPLETED

    build_artifact = mocked_session.query(orm.BuildArtifact).filter_by(id=1).first()
    assert build_artifact.artifact_type == schema.BuildArtifactType.LOCKFILE

    # test relationship resolutions
    assert build.build_artifacts[0].id == build_artifact.id
    # https://github.com/resulyrt93/pytest-sqlalchemy-mock/issues/6
    # for some reason it's not liking to resolve the through relationship
    # assert build.package_builds != []


def test_get_build_lockfile(mocked_session):
    response_text = api.get_build_lockfile(mocked_session, 1)
    lines = response_text.split("\n")
    for indx, line in enumerate(lines):
        if indx == 0:
            assert line.startswith("# platform")
            continue

        if indx == 1:
            assert line == "@EXPLICIT"
            continue

        # https://github.com/resulyrt93/pytest-sqlalchemy-mock/issues/6
        # for some reason it's not liking to resolve the through relationship
        # if indx == 2:
        #     assert "https://conda.anaconda.org/conda-forge/linux-64/icu-70.1-h27087fc_0.conda#87473a15119779e021c314249d4b4aed"
        #
        # if indx == 3:
        #     assert "https://conda.anaconda.org/conda-forge/linux-64/zarr-2.12.0-pyhd8ed1ab_0.tar.bz2#37d4251d34eb991ff9e40e546cc2e803"
