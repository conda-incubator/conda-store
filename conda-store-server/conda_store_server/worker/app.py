import logging

from traitlets import Unicode, Integer, List
from traitlets.config import Application

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

    config_file = Unicode(
        "conda_store_config.py", help="config file to load for conda-store", config=True
    )

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.load_config_file(self.config_file)

    @property
    def conda_store(self):
        if hasattr(self, "_conda_store"):
            return self._conda_store

        self._conda_store = CondaStore(parent=self, log=self.log)
        return self._conda_store

    def start(self):
        argv = [
            "worker",
            "--loglevel=INFO",
            "--beat",
        ]
        self.conda_store.ensure_directories()
        self.conda_store.celery_app.worker_main(argv)
