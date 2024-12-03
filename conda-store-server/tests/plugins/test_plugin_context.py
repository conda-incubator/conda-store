# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import io
import logging
import os
import subprocess
import sys

import pytest

from conda_store_server.plugins.plugin_context import PluginContext


def test_run_command_no_logs():
    out = io.StringIO()
    err = io.StringIO()
    context = PluginContext(stdout=out, stderr=err, log_level=logging.ERROR)

    context.run_command(["echo", "testing"])
    assert err.getvalue() == ""
    assert out.getvalue() == "testing\n"


def test_run_command_log_info():
    out = io.StringIO()
    err = io.StringIO()
    context = PluginContext(stdout=out, stderr=err, log_level=logging.INFO)

    context.run_command(["echo", "testing"])
    assert err.getvalue() == ""
    assert (
        out.getvalue()
        == """Running command: ['echo', 'testing']
testing
"""
    )


def test_run_command_errors():
    context = PluginContext(log_level=logging.ERROR)

    with pytest.raises(subprocess.CalledProcessError):
        context.run_command(["conda-store-server", "-thiswillreturnanonzeroexitcode"])


@pytest.mark.skipif(
    sys.platform == "win32", reason="stat is not a valid command on Windows"
)
def test_run_command_kwargs():
    """Ensure that kwargs get passed to subprocess"""
    out = io.StringIO()
    err = io.StringIO()
    context = PluginContext(stdout=out, stderr=err, log_level=logging.ERROR)

    # set the cwd to this directory and check that this file exists
    dir_path = os.path.dirname(os.path.realpath(__file__))
    context.run_command(["stat", "test_plugin_context.py"], check=True, cwd=dir_path)
    assert err.getvalue() == ""
    assert "File: test_plugin_context.py" in out.getvalue()
