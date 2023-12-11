---
description: Contribute to conda-store's codebase
---

# Contribute code

:::warning
This page is in active development, content may be inaccurate and incomplete.
:::

## Set up development environment - conda-store-core

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
| conda-store web server | [localhost:8080](http://localhost:8080)| `admin` | `password`|
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
# replace this with environment-macos-dev.yaml or environment-windows-dev.yaml
# if you are on Mac or Windows
conda env create -f conda-store-server/environment-dev.yaml
conda activate conda-store-server-dev
```

3. Running `conda-store` in `--standalone` mode launches celery as a
subprocess of the web server.

```
python -m conda_store_server.server --standalone
```

4. Visit [localhost:8080](http://localhost:8080/)

## Set up development environment -- conda-store-ui

To get started with conda-store-ui development, there are a couple of options. This guide will help you to set up your local development environment.

### Prerequisites

Before setting up conda-store ui, you must prepare your environment.

We use [Docker Compose](https://docs.docker.com/compose/) to set up the infrastructure before starting ensure that you have docker-compose installed. If you need to install docker-compose, please see their [installation documentation](https://docs.docker.com/compose/install/)

1. Clone the [conda-store-ui](https://github.com/conda-incubator/conda-store-ui.git) repository.
2. Copy `.env.example` to `.env`. All default settings should work, but if you want to test against a differenct version of conda-store-server, you can specify if in the `.env` file by setting the `CONDA_STORE_SERVER_VERSION` variable to the desired version

### Local Development with conda-store-ui running in Docker

Running conda-store-ui in Docker is the simplest way to setup your local development environment.

1. Run `yarn run start:docker` to start the entire development stack.
2. Open you local browser and go to [http://localhost:8000](http://localhost:8000) so see conda-store-ui.
3. You can then login using the default username of `username` and default password of `password`.

**Note:** Hot reloading is enabled, so when you make changes to source files, your browser will reload and reflect the changes.

### Local Development without running conda-store-ui in Docker

This setup still uses Docker for supporting services but runs conda-store-ui locally.

#### Set up your environment

This project uses [Conda](https://conda.io) for package management. To set up Conda, please see their [installation documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).
1. Change to the project root ` cd conda-store-ui`
2. From the project root create the conda environment `conda env create -f environment_dev.yml`
3. Activate the development environment `conda activate cs-ui-dev-env`
4. Install yarn dependencies `yarn install`

#### Run the application

1. Run `yarn run start` and wait for the application to finish starting up
2. Open you local browser and go to [http://localhost:8000](http://localhost:8000) so see conda-store-ui.
3. You can then login using the default username of `username` and default password of `password`.

**Note:** Hot reloading is enabled, so when you make changes to source files, your browser will reload and reflect the changes.

<!-- TODO

## jupyterlab-conda-store

-->

## Workflows

### Changes to API

The REST API is considered somewhat stable. If any changes are made to
the API make sure the update the OpenAPI/Swagger specification in
`docs/_static/openapi.json`. This may be downloaded from the `/docs`
endpoint when running conda-store. Ensure that the
`c.CondaStoreServer.url_prefix` is set to `/` when generating the
endpoints.
<!-- TODO -->

## Workflows

### Changes to API

The REST API is considered somewhat stable. If any changes are made to
the API make sure the update the OpenAPI/Swagger specification in
`docs/_static/openapi.json`. This may be downloaded from the `/docs`
endpoint when running conda-store. Ensure that the
`c.CondaStoreServer.url_prefix` is set to `/` when generating the
endpoints.
