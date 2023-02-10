import pytest
from conda_store_server.utils import extract_tarball_extension


@pytest.mark.parametrize(
    "package_tarball_full_path, expected",
    [
        # single ext
        ("blah.conda", ".conda"),
        ("blah.zip", ".zip"),
        ("blah-4.33.tar", ".tar"),
        # double ext
        ("blah.tar.gz", ".tar.gz"),
        ("blah.tar.bz2", ".tar.bz2"),
        # paths with dots in names
        ("blah-4.33-h12300_0.conda", ".conda"),
        ("blah-4.33-h12300_0.zip", ".zip"),
        ("blah-4.33-h12300_0.tar", ".tar"),
        ("blah-4.33-h12300_0.tar.gz", ".tar.gz"),
        ("blah-4.33-h12300_0.tar.bz2", ".tar.bz2"),
        # bad paths
        ("nada/nada", None),
    ],
)
def test_extract_tarball_extension(package_tarball_full_path, expected):
    actual = extract_tarball_extension(package_tarball_full_path)
    assert actual == expected


