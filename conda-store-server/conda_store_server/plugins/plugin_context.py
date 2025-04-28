# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import io
import logging
import subprocess
import uuid


class PluginContext:
    """The plugin context provides some useful attributes and functions to a hook.

    This includes
        * the variables: conda_store, log, stdout, stderr, namespace, environment
        * the functions: run_command

    Attributes
    ----------
    conda_store : conda_store_server.conda_store
        conda_store instance
    log_level : int
        logging level
    stdout : io.StringIO
        stream to write command output to
    stderr : io.StringIO
        stream to write command error output to
    namespace : str
        namespace context the plugin is running in
    environment : str
        environment context the plugin is running in
    """

    def __init__(
        self,
        conda_store,
        stdout: io.StringIO | None = None,
        stderr: io.StringIO | None = None,
        log_level: int = logging.INFO,
        namespace: str | None = None,
        environment: str | None = None,
    ):
        if stdout is not None and stderr is None:
            stderr = stdout

        self.id = str(uuid.uuid4())
        self.stdout = stdout if stdout is not None else io.StringIO()
        self.stderr = stderr if stderr is not None else io.StringIO()
        self.log = logging.getLogger(
            f"conda_store_server.plugins.plugin_context.{self.id}"
        )
        self.log.propagate = False
        self.log.addHandler(logging.StreamHandler(stream=self.stdout))
        self.log.setLevel(log_level)
        self.conda_store = conda_store
        self.namespace = namespace
        self.environment = environment

    def run_command(self, command: str, redirect_stderr: bool = True, **kwargs):
        """Runs command and immediately writes to logs"""
        self.log.info("Running command: %s", command)

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
        ) as proc:
            for line in proc.stdout:
                self.stdout.write(line)
            if not redirect_stderr:
                for line in proc.stderr:
                    self.stderr.write(line)

        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, proc.args)
