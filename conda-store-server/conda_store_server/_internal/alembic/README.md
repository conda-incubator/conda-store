# Alembic

## Generating a database migration

If the database needs to be changed, `alembic` can be used to generate the migration scripts to do
so. This is usually painless, and follows these steps:

1. Make changes to the database models in
   `conda-store-server/conda_store_server/_internal/orm.py`.
2. `alembic` will examine a running `conda-store` database and compare the
   tables it finds there with changes to tables it finds in `orm.py` in your
   feature branch. To do this, you need a running `conda-store` database from
   the `main` branch, so clone the `conda-store` somewhere else on disk.
3. `cd` to the `main` branch in the _other_ copy of `conda-store`, and start
    all the services with `docker compose up --build`. This will get a local
    `conda-store` instance up and running, including the database that `alembic`
    needs.
4. In another terminal, `cd` to your working branch and run `alembic revision
   --autogenerate -m "<some useful comment about what changed in the database>`.
   `alembic` will compare the running `postgres` database you started in step 3
   with what it finds in your working branch, and create a database migration.
5. If the migration looks good, add and commit it to the repository.
