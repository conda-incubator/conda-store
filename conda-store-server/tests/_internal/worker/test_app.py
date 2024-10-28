# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest
import logging

from unittest.mock import patch

from conda_store_server._internal.worker.app import CondaStoreWorker


def test_worker_with_valid_config(conda_store_config, tmp_path):
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


def test_worker_with_invalid_config(conda_store_config):
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
        ]
)
def test_logger_to_celery_logging_level(logging_level, output):
    worker = CondaStoreWorker()
    celery_logging_level = worker.logger_to_celery_logging_level(logging_level)
    assert celery_logging_level == output
