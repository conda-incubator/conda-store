from conda_store_server.utils import disk_usage, du

# TODO: Add tests for the other functions in utils.py


def test_disk_usage(tmp_path):
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # This varies across OSes
    dir_size = du(test_dir)
    assert abs(dir_size - int(disk_usage(test_dir))) <= 1000

    test_file = test_dir / "test_file"
    test_file.write_text("a" * 1000)
    test_file2 = test_dir / "test_file2"
    test_file2.write_text("b" * 1000)
    # Test hard links
    test_file_hardlink = test_dir / "test_file_hardlink"
    test_file_hardlink.hardlink_to(test_file)

    # The exact values depend on the block size and other details. Just check
    # that it is in the right range. Note that disk_usage uses the du command
    # on Mac and Linux but uses the Python du() function on Windows.
    val = disk_usage(test_file)
    assert isinstance(val, str)
    assert 1000 <= int(val) <= 1500
    assert 1000 <= du(test_file) <= 1500

    val = disk_usage(test_dir)
    assert isinstance(val, str)
    assert 2000 + dir_size <= int(val) <= 2700 + dir_size
    assert 2000 + dir_size <= du(test_dir) <= 2700 + dir_size
