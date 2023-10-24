import contextlib
import functools
import io
import logging
import subprocess
import tempfile
import typing
import uuid

from conda_store_server import utils


def action(f: typing.Callable):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        action_context = ActionContext()
        with contextlib.ExitStack() as stack:
            # redirect stdout -> action_context.stdout
            stack.enter_context(contextlib.redirect_stdout(action_context.stdout))

            # redirect stderr -> action_context.stdout
            stack.enter_context(contextlib.redirect_stderr(action_context.stdout))

            # create a temporary directory
            tmpdir = stack.enter_context(tempfile.TemporaryDirectory())

            # enter temporary directory
            stack.enter_context(utils.chdir(tmpdir))

            # run function and store result
            action_context.result = f(action_context, *args, **kwargs)
        return action_context

    return wrapper


class ActionContext:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.log = logging.getLogger(f"conda_store_server.action.{self.id}")
        self.log.propagate = False
        self.log.addHandler(logging.StreamHandler(stream=self.stdout))
        self.log.setLevel(logging.INFO)
        self.result = None
        self.artifacts = {}

    def run(self, *args, redirect_stderr=True, **kwargs):
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
