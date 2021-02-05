import pathlib

import pytest


@pytest.mark.xfail
def test_build(conda_store, mocker):
    environment_filename = 'tests/assets/environments/conda-store.yaml'

    def fake_conda_install(conda_store, build_path, tmp_environment_filename):
        pathlib.Path(build_path).mkdir(parents=True, exist_ok=True)
        return 'I ran'

    mocker.patch(
        'conda_store.build.build_conda_install',
        fake_conda_install
    )
    mocker.patch(
        'conda_store.build.build_conda_pack',
        return_value=None
    )
    mocker.patch(
        'conda_store.build.build_docker_image',
        return_value=None
    )

    from conda_store import build
    conda_store.register_environment(environment_filename)
    build.conda_build(conda_store)
