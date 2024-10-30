# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging
import sys
from unittest.mock import patch

import pytest
from traitlets.config import Config

from conda_store_server._internal.worker.app import CondaStoreWorker


class MockCeleryApp:
    def worker_main(argv):
        pass


@pytest.mark.skipif(
    sys.platform == "win32", reason="celery beat is not supported on windows"
)
@patch("conda_store_server.app.CondaStore.celery_app")
def test_start_worker(mock_celery_app, conda_store_config):
    """Test that the celery worker is started with the right arguments"""
    mock_celery_app.return_value = MockCeleryApp()
    conda_store_config["CondaStoreWorker"] = Config(
        dict(
            log_level=logging.WARN,
            watch_paths=["/opt/environments"],
            concurrency=4,
        )
    )
    worker = CondaStoreWorker(config=conda_store_config)
    worker.initialize()
    worker.start()
    mock_celery_app.worker_main.assert_called_with(
        [
            "worker",
            "--loglevel=WARNING",
            "--max-tasks-per-child=10",
            "--beat",
            "--concurrency=4",
        ]
    )


def test_initialize_worker_with_valid_config_file(conda_store_config, tmp_path):
    """Test that a worker is able to init when the provided config file exists"""
    config_file_contents = """
import logging
c.CondaStoreWorker.log_level = logging.INFO
c.CondaStoreWorker.watch_paths = ["/opt/environments"]
c.CondaStoreWorker.concurrency = 4
"""
    test_config_file = str(tmp_path / "config1")
    with open(test_config_file, "w") as file:
        file.write(config_file_contents)

    worker = CondaStoreWorker(config=conda_store_config)
    worker.config_file = test_config_file
    worker.initialize()


def test_initialize_worker_with_invalid_config(conda_store_config):
    """Test that a worker is not able to init if the provided config file does not exist"""
    worker = CondaStoreWorker(config=conda_store_config)
    with pytest.raises(SystemExit) as exc_info:
        worker.config_file = "/i/dont/exist"
        worker.initialize()

    assert exc_info.value.code == 1


@pytest.mark.parametrize(
    "logging_level,output",
    [
        (logging.INFO, "INFO"),
        (logging.CRITICAL, "CRITICAL"),
        (logging.FATAL, "CRITICAL"),
        (logging.WARN, "WARNING"),
    ],
)
def test_logger_to_celery_logging_level(logging_level, output):
    worker = CondaStoreWorker()
    celery_logging_level = worker.logger_to_celery_logging_level(logging_level)
    assert celery_logging_level == output
