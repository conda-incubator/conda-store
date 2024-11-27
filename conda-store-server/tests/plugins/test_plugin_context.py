# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging
import os
import subprocess

import pytest

from conda_store_server.plugins.plugin_context import PluginContext


class TestOutPutCapture:
    def __init__(self):
        self.output = ""

    def write(self, line: str):
        self.output += line


def test_run_command_no_logs():
    out = TestOutPutCapture()
    err = TestOutPutCapture()
    pr = PluginContext(stdout=out, stderr=err, log_level=logging.ERROR)

    pr.run_command(["echo", "testing"])
    assert err.output == ""
    assert out.output == "testing\n"


def test_run_command_log_info():
    out = TestOutPutCapture()
    err = TestOutPutCapture()
    pr = PluginContext(stdout=out, stderr=err, log_level=logging.INFO)

    pr.run_command(["echo", "testing"])
    assert err.output == ""
    assert (
        out.output
        == """Running command: ['echo', 'testing']
testing
"""
    )


def test_run_command_errors():
    out = TestOutPutCapture()
    err = TestOutPutCapture()
    pr = PluginContext(stdout=out, stderr=err, log_level=logging.ERROR)

    with pytest.raises(subprocess.CalledProcessError):
        pr.run_command(["conda-store-server", "-thiswillreturnanonzeroexitcode"])


def test_run_command_kwargs():
    """Ensure that kwargs get passed to subprocess"""
    out = TestOutPutCapture()
    err = TestOutPutCapture()
    pr = PluginContext(stdout=out, stderr=err, log_level=logging.ERROR)

    # set the cwd to this directory and check that this file exists
    dir_path = os.path.dirname(os.path.realpath(__file__))
    pr.run_command(["stat", "test_plugin_context.py"], check=True, cwd=dir_path)
    assert err.output == ""
    assert "File: test_plugin_context.py" in out.output
