# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest
from conda_store_server._internal.utils import disk_usage, du, retry_on_errors

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


class MyTestError(Exception):
    pass


def test_retry_on_error():
    class MyTestClass():
        def __init__(self):
            self.called = 0

        @retry_on_errors(allowed_retries=1, on_errors=(MyTestError))
        def raise_my_test_exception(self):
            self.called += 1
            raise MyTestError
    
    tc = MyTestClass()
    
    with pytest.raises(MyTestError):
        tc.raise_my_test_exception()

    assert tc.called == 2


def test_retry_on_not_covered_error():
    class MyTestClass():
        def __init__(self):
            self.called = 0

        @retry_on_errors(allowed_retries=1, on_errors=(IndexError))
        def raise_my_test_exception(self):
            self.called += 1
            raise MyTestError
    
    tc = MyTestClass()
    
    with pytest.raises(MyTestError):
        tc.raise_my_test_exception()
    
    assert tc.called == 1


def test_retry_no_error():
    @retry_on_errors(allowed_retries=1, on_errors=(MyTestError))
    def test_function():
        return 1
    
    result = test_function()
    assert result == 1
