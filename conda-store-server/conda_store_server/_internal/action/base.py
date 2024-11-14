# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import contextlib
import functools
import io
import logging
import subprocess
import tempfile
import time
import typing
import uuid

from conda_store_server._internal import utils


def action(f: typing.Callable):
    @functools.wraps(f)
    def wrapper(*args, stdout=None, stderr=None, **kwargs):
        action_context = ActionContext(stdout=stdout, stderr=stderr)
        with contextlib.ExitStack() as stack:
            # redirect stdout -> action_context.stdout
            stack.enter_context(contextlib.redirect_stdout(action_context.stdout))

            # redirect stderr -> action_context.stdout
            stack.enter_context(contextlib.redirect_stderr(action_context.stdout))

            # create a temporary directory
            tmpdir = stack.enter_context(tempfile.TemporaryDirectory())

            # enter temporary directory
            stack.enter_context(utils.chdir(tmpdir))

            start_time = time.monotonic()

            # run function and store result
            action_context.result = f(action_context, *args, **kwargs)
            action_context.log.info(
                f"Action {f.__name__} completed in {time.monotonic() - start_time:.3f} s."
            )

        return action_context

    return wrapper


class ActionContext:
    def __init__(self, stdout=None, stderr=None):
        if stdout is not None and stderr is None:
            stderr = stdout

        self.id = str(uuid.uuid4())
        self.stdout = stdout if stdout is not None else io.StringIO()
        self.stderr = stderr if stderr is not None else io.StringIO()
        self.log = logging.getLogger(f"conda_store_server._internal.action.{self.id}")
        self.log.propagate = False
        self.log.addHandler(logging.StreamHandler(stream=self.stdout))
        self.log.setLevel(logging.INFO)
        self.result = None
        self.artifacts = {}

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
