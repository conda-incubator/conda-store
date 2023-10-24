import logging
import os
import sys

from conda_store_server.app import CondaStore
from traitlets import Integer, List, Unicode, validate
from traitlets.config import Application, catch_config_error


class CondaStoreWorker(Application):
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
