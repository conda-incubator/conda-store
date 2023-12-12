---
description: Install conda-store
---

# Database architecture

:::warning
This page is in active development, some content may be inaccurate.
:::

## Model

At a high level the database model can be described in the image
bellow.

![high level diagram](../images/conda-store-database-architecture.png)

Important things to note about the relationship:

- An `environment` exists within a given `namespace` and always has a current `build`
- A `build` belongs to a particular `environment` and has associated `condapackage` and `buildartfacts`
- A `buildartifact` is a way for the database to keep track of
  external resources for example s3 artifacts, filesystem directories,
  etc
- A `condapackage` is a representation of a given Conda package which belongs to a given `condachannel`
- A `specification` is the environment.yaml using in `conda env create -f <environment.yaml>`

The following will generate the database model shown bellow. It was
generated from the `examples/docker` example. You'll see in the
command that we are excluding several tables. These tables are managed
by [celery](https://docs.celeryproject.org/en/stable/).

```shell
pip install eralchemy  # not available on conda-forge
eralchemy -i "postgresql+psycopg2://admin:password@localhost:5432/conda-store"  \
    -x celery_tasksetmeta celery_taskmeta kombu_queue kombu_message alembic_version \
    -o output.png
```

![entity relationship diagram](../images/conda-store-entity-relationship-diagram.png)

## Migrations

conda-store relies on [SQLAlchemy](https://www.sqlalchemy.org/) for ORM mapping, and on [Alembic](https://alembic.sqlalchemy.org/en/latest/) for DB migrations.

The procedure to modify the database is the following :

- First, modify [the ORM Model](https://github.com/conda-incubator/conda-store/blob/main/conda-store-server/conda_store_server/orm.py) according to the changes you want to make
- edit the file `conda-store-server/alembic.ini` and replace the value for entry `sqlalchemy.url` to match the connection URL of your database.

For example (when postgres was started via docker-compose):
```
script_location = alembic
sqlalchemy.url = postgresql+psycopg2://postgres:password@localhost:5432/conda-store
```

- in your command line, run the following :

```sh
cd conda-store-server/conda_store_server
alembic revision --autogenerate -m "description of your changes"
```

- You should have a new file in `conda-store-server/conda_store_server/alembic/versions/` . **Review it thoroughly**. It contains the [`alembic` operations](https://alembic.sqlalchemy.org/en/latest/ops.html) (`op`) to actually modify the database, either when upgrading (`upgrade` function) or downgrading (`downgrade`)

- You can migrate your data within these `upgrade`/`downgrade` functions, for example :

```python
from alembic import op

# revision identifiers, used by Alembic.
revision = 'abcdef01234567'
down_revision = '987654321f0edc'
branch_labels = None
depends_on = None

def upgrade():

    # operations to modify the database structure
    # ...
    op.create_table(
        'new_table',
        Column('id', INTEGER, primary_key=True),
        Column('field1', VARCHAR(50), nullable=False),
        Column('field2', INTEGER),
        Column('timestamp', TIMESTAMP, server_default=func.now())
    )
    # ...

    op.execute('''INSERT INTO new_table (field1, field2)
                  SELECT field1, field2
                  FROM old_table''')

    # other operations to modify the database structure
    # ...


def downgrade():

    op.drop_table('new_table')

```

- Once you're sure about the changes generated, you can apply them by running :

```sh
alembic upgrade head
```

- Check your database : your changes should be reflected. If not, refer to [Alembic's documentation](https://alembic.sqlalchemy.org/en/latest/).
