# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pytest
import datetime

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from conda_store_server import api
from conda_store_server._internal import orm


def test_add_build_archived_on_column_basic(
    conda_store, alembic_config, alembic_runner
):
    """Simply run the upgrade and downgrade for this migration"""
    # migrate all the way to the target revision
    alembic_runner.migrate_up_to("8c5abec6e601")

    # ensure the archived_on column exists
    with conda_store.session_factory() as db:
        db.execute(text("SELECT archived_on from build"))

    # try downgrading
    alembic_runner.migrate_down_one()

    # ensure the archived_on column does not exists
    with conda_store.session_factory() as db:
        with pytest.raises(OperationalError):
            db.execute(text("SELECT archived_on from build"))

    # try upgrading once more
    alembic_runner.migrate_up_one()

    # ensure the archived_on column exists
    with conda_store.session_factory() as db:
        db.execute(text("SELECT archived_on from build"))


def test_downgrade_works_for_populated_column(
    conda_store, alembic_config, alembic_runner, seed_conda_store
):
    """Try to run the downgrade part of the migration when the `archived_on` column has data"""
    # migrate all the way to the target revision
    alembic_runner.migrate_up_to("8c5abec6e601")

    # ensure the archived_on column exists
    with conda_store.session_factory() as db:
        db.execute(text("SELECT archived_on from build"))

    # update demo data to have data in archived_on column
    with conda_store.session_factory() as db:
        build = api.get_build(db, 1)
        build.archived_on = datetime.datetime.now(datetime.UTC)
        db.commit()

    # try downgrading
    alembic_runner.migrate_down_one()

    # ensure the archived_on column does not exists
    with conda_store.session_factory() as db:
        with pytest.raises(OperationalError):
            db.execute(text("SELECT archived_on from build"))
