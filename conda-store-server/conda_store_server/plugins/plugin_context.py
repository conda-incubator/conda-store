# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import io
import logging
import subprocess
import uuid


class PluginContext:
    """The plugin context provides some useful attributes to a hook.

    This includes
        * the variables: conda_store, log, stdout, stderr
        * the functions: run_command, run
    """
    def __init__(self, conda_store=None, stdout=None, stderr=None, log_level=logging.INFO):
        if stdout is not None and stderr is None:
            stderr = stdout

        self.id = str(uuid.uuid4())
        self.stdout = stdout if stdout is not None else io.StringIO()
        self.stderr = stderr if stderr is not None else io.StringIO()
        self.log = logging.getLogger(f"conda_store_server.plugins.plugin_context.{self.id}")
        self.log.propagate = False
        self.log.addHandler(logging.StreamHandler(stream=self.stdout))
        self.log.setLevel(log_level)
        self.conda_store = conda_store

    def run_command(self, command, redirect_stderr=True, **kwargs):
        """Runs command and immediately writes to logs"""
        self.log.info(f"Running command: {' '.join(command)}")

        # Unlike subprocess.run, Popen doesn't support the check argument, so
        # ignore it. The code below always checks the return code
        kwargs.pop("check", None)

        # https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT if redirect_stderr else subprocess.PIPE,
            bufsize=1,
            universal_newlines=True,
            **kwargs,
        ) as p:
            for line in p.stdout:
                self.stdout.write(line)
            if not redirect_stderr:
                for line in p.stderr:
                    self.stderr.write(line)

        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, p.args)

    def run(self, *args, redirect_stderr=True, **kwargs):
        """Runs command waiting for it to succeed before writing to logs"""
        result = subprocess.run(
            *args,
            **kwargs,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT if redirect_stderr else subprocess.PIPE,
            encoding="utf-8",
        )
        self.stdout.write(result.stdout)
        if not redirect_stderr:
            self.stderr.write(result.stderr)
        return result