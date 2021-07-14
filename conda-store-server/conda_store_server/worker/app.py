import logging

from traitlets import Unicode, Integer, List
from traitlets.config import Application

from conda_store_server import build
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

    storage_threshold = Integer(
        5 * (2 ** 30),
        help="emit warning when free disk space drops below storage threshold bytes",
        config=True,
    )

    poll_interval = Integer(
        10,
        help="poll interval to check environment directory for new environments",
        config=True,
    )

    watch_paths = List(
        [],
        help="set of directories or filenames to watch for conda environment changes",
        config=True,
    )

    config_file = Unicode(
        "conda_store_config.py", help="config file to load for conda-store", config=True
    )

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.log.info(f"reading configuration file {self.config_file}")
        self.load_config_file(self.config_file)

    def start(self):
        conda_store = CondaStore(parent=self, log=self.log)
        conda_store.ensure_directories()

        conda_store.update_storage_metrics()
        conda_store.update_conda_channels()

        build.start_conda_build(
            conda_store, self.watch_paths, self.storage_threshold, self.poll_interval
        )
