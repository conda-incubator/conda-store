import logging
import os
import sys

from traitlets import Unicode, Integer, List, validate
from traitlets.config import Application, catch_config_error

from conda_store_server.app import CondaStore


class CondaStoreWorker(Application):
    aliases = {
        "config": "CondaStoreWorker.config_file",
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
                "ERROR: Failed to find specified config file: {}".format(
                    proposal.value
                ),
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

    def start(self):
        argv = [
            "worker",
            "--loglevel=INFO",
            "--beat",
        ]

        if self.concurrency:
            argv.append(f"--concurrency={self.concurrency}")

        self.conda_store.ensure_directories()
        self.conda_store.celery_app.worker_main(argv)
