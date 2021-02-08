import pytest

from conda_store import orm


@pytest.mark.parametrize('channel', [
    'conda-forge',
    'https://repo.anaconda.com/pkgs/main'
])
def test_add_conda_channel_packages(db, channel):
    orm.CondaPackage.add_channel_packages(db, channel)


def test_add_conda_channel_packages_duplicate(db):
    """Test to make sure that database does not throw errors when
    duplicate packages are processed

    """

    channel = 'https://repo.anaconda.com/pkgs/main'
    orm.CondaPackage.add_channel_packages(db, channel)
    orm.CondaPackage.add_channel_packages(db, channel)
