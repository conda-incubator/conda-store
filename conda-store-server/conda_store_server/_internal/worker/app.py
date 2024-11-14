# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging
import os
import sys

from traitlets import Integer, List, Unicode, validate
from traitlets.config import Application, catch_config_error

from conda_store_server import __version__
from conda_store_server.app import CondaStore


class CondaStoreWorker(Application):
    version = __version__
    aliases = {
        "config": "CondaStoreWorker.config_file",
    }

    flags = {
        "standalone": (
            {
                "CondaStoreServer": {
                    "standalone": True,
                }
            },
            "Run conda-store-server in standalone mode with celery worker as a subprocess of webserver",
        ),
    }

    log_level = Integer(
        logging.INFO,
        help="log level to use",
        config=True,
    )

    watch_paths = List(
        [], help="list of paths to watch for environment changes", config=True
    )

    concurrency = Integer(
        None,
        help="Number of worker threads to spawn. Limit the concurrency of conda-builds",
        config=True,
        allow_none=True,
    )

    config_file = Unicode(
        help="config file to load for conda-store",
        config=True,
    )

    @validate("config_file")
    def _validate_config_file(self, proposal):
        if not os.path.isfile(proposal.value):
            print(
                f"ERROR: Failed to find specified config file: {proposal.value}",
                file=sys.stderr,
            )
            sys.exit(1)
        return proposal.value

    @catch_config_error
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)

        self.conda_store = CondaStore(parent=self, log=self.log)

        # ensure checks on redis_url
        self.conda_store.redis_url

    def logger_to_celery_logging_level(self, logging_level):
        # celery supports the log levels DEBUG | INFO | WARNING | ERROR | CRITICAL | FATAL
        # https://docs.celeryq.dev/en/main/reference/cli.html#celery-worker
        logging_to_celery_level_map = {
            50: "CRITICAL",
            40: "ERROR",
            30: "WARNING",
            20: "INFO",
            10: "DEBUG",
        }
        return logging_to_celery_level_map[logging_level]

    def start(self):
        argv = [
            "worker",
            f"--loglevel={self.logger_to_celery_logging_level(self.log_level)}",
            "--max-tasks-per-child=10",  # mitigate memory leaks
        ]

        # The default Celery pool requires this on Windows. See
        # https://stackoverflow.com/questions/37255548/how-to-run-celery-on-windows
        if sys.platform == "win32":
            os.environ.setdefault("FORKED_BY_MULTIPROCESSING", "1")
        else:
            # --beat does not work on Windows
            argv += [
                "--beat",
            ]

        if self.concurrency:
            argv.append(f"--concurrency={self.concurrency}")

        self.conda_store.ensure_directories()
        self.conda_store.celery_app.worker_main(argv)
