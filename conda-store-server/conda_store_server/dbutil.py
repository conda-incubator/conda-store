import os
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

_here = os.path.abspath(os.path.dirname(__file__))

ALEMBIC_INI_TEMPLATE_PATH = os.path.join(_here, "alembic.ini")
ALEMBIC_DIR = os.path.join(_here, "alembic")


def write_alembic_ini(alembic_ini, db_url):
    """Write a complete alembic.ini from a template.

    Parameters
    ----------
    alembic_ini : str
        path to the alembic.ini file that should be written.
    db_url : str
        The SQLAlchemy database url
    """
    with open(ALEMBIC_INI_TEMPLATE_PATH) as f:
        alembic_ini_tpl = f.read()

    with open(alembic_ini, "w") as f:
        f.write(
            alembic_ini_tpl.format(
                alembic_dir=ALEMBIC_DIR,
                # If there are any %s in the URL, they should be replaced with %%, since ConfigParser
                # by default uses %() for substitution. You'll get %s in your URL when you have usernames
                # with special chars (such as '@') that need to be URL encoded. URL Encoding is done with %s.
                # YAY for nested templates?
                db_url=str(db_url).replace("%", "%%"),
            )
        )


@contextmanager
def _temp_alembic_ini(db_url):
    """Context manager for temporary JupyterHub alembic directory

    Temporarily write an alembic.ini file for use with alembic migration scripts.

    Context manager yields alembic.ini path.

    Parameters
    ----------
    db_url : str
        The SQLAlchemy database url, e.g. `sqlite:///jupyterhub.sqlite`.

    Returns
    -------
    alembic_ini: str
        The path to the temporary alembic.ini that we have created.
        This file will be cleaned up on exit from the context manager.
    """
    with TemporaryDirectory() as td:
        alembic_ini = os.path.join(td, "alembic.ini")
        write_alembic_ini(alembic_ini, db_url)
        yield alembic_ini


def upgrade(db_url, revision="head"):
    """Upgrade the given database to revision.

    db_url: str
        The SQLAlchemy database url, e.g. `sqlite:///jupyterhub.sqlite`.
    revision: str [default: head]
        The alembic revision to upgrade to.
    """
    engine = create_engine(db_url)

    # retrieves the names of tables in the DB
    current_table_names = set(inspect(engine).get_table_names())

    with _temp_alembic_ini(db_url) as alembic_ini:
        alembic_cfg = Config(alembic_ini)

        if (
            "alembic_version" not in current_table_names
            and len(current_table_names) > 0
        ):
            # If table alembic_version is missing,
            # we stamp the revision at the first one, that introduces the alembic revisions.
            # I chose the leave the revision number hardcoded as it's not something
            # dynamic, not something we want to change, and tightly related to the codebase
            command.stamp(alembic_cfg, "48be4072fe58")
            # After this point, whatever is in the database, Alembic will
            # believe it's at the first revision. If there are more upgrades/migrations
            # to run, they'll be at the next step :

        # run the upgrade.
        command.upgrade(config=alembic_cfg, revision=revision)
