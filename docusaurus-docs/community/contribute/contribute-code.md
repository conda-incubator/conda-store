---
description: Contribute to conda-store's codebase
---

# Contribute code

:::warning
This page is in active development, content may be inaccurate and incomplete.
:::

## Set up development environment

### Docker (recommended)

Install the following dependencies before developing on conda-store.

- [docker](https://docs.docker.com/engine/install/)
- [docker-compose](https://docs.docker.com/compose/install/)

To deploy `conda-store` run the following command

```shell
docker-compose up --build -d
```

:::important
Many of the conda-store docker images are built/tested for amd64(x86-64)
there will be a performance impact when building and running on
arm architectures. Otherwise this workflow has been shown to run and build on OSX.
Notice the `architecture: amd64` whithin the docker-compose.yaml files.
:::

The following resources will be available:

| Resource | Localhost port | username | password |
|----------|----------------|----------|----------|
| conda-store web server | [localhost:5000](http://localhost:5000)| `admin` | `password`|
| [JupyterHub](https://jupyter.org/hub) | [localhost:8000](http://localhost:8000) | any | `test` |
| [MinIO](https://min.io/) S3 |  [localhost:9000](http://localhost:9000) | `admin` | `password` |
| [PostgreSQL](https://www.postgresql.org/) (database: `conda-store`)| [localhost:5432](http://localhost:5432) | `admin` | `password` |
| [Redis](https://www.redis.com/) |  [localhost:6379](http://localhost:6379) | - | password |

On a fast machine this deployment should only take 10 or so seconds
assuming the docker images have been partially built before.

If you are making and changes to conda-store-server and would like to see
those changes in the deployment, run:

```shell
docker-compose down -v # not always necessary
docker-compose up --build
```

### Linux

1. Install the following dependencies before developing on conda-store:

- [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)

2. Install the development dependencies and activate the environment:

```shell
conda env create -f conda-store-server/environment-dev.yaml
conda activate conda-store-server-dev
```

3. Running `conda-store` in `--standalone` mode launches celery as a
subprocess of the web server.

```shell
python -m conda_store_server.server --standalone tests/assets/conda_store_standalone_config.py
```

4. Visit [localhost:8080](http://localhost:8080/)

## conda-store-ui

<!-- TODO -->

## jupyterlab-conda-store

<!-- TODO -->

## Workflows

### Changes to API

The REST API is considered somewhat stable. If any changes are made to
the API make sure the update the OpenAPI/Swagger specification in
`docs/_static/openapi.json`. This may be downloaded from the `/docs`
endpoint when running conda-store. Ensure that the
`c.CondaStoreServer.url_prefix` is set to `/` when generating the
endpoints.
