import logging
import os

from conda_store.utils import disk_usage, free_disk_space, total_disk_space

logger = logging.getLogger(__name__)


def initialize_conda_store_state(dbm):
    with dbm.transaction() as cursor:
        cursor.execute('INSERT OR IGNORE INTO conda_store (id) VALUES (1)')


def calculate_storage_metrics(dbm, conda_store_path):
    with dbm.transaction() as cursor:
        cursor.execute('''
          UPDATE conda_store
          SET
            disk_usage = ?,
            free_storage = ?,
            total_storage = ?
          WHERE id = 1
        ''', (
            disk_usage(conda_store_path),
            free_disk_space(conda_store_path),
            total_disk_space(conda_store_path)))
