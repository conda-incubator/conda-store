---
sidebar_position: 4
description: Local development setup for conda-store
---

# Local setup for conda-store (core)

Once you have a [local copy of the `conda-store` repository](community/contribute/contribute-code#setup-for-local-development), you can set up your development environment.

There are two main ways to set up your local environment for development:

- Using [Docker and Docker compose(recommended)](#docker-recommended)
- Local development [without Docker](#without-docker)

## Docker (recommended)

### Pre-requisites

Install the following dependencies before developing on conda-store:

- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/install/)

### Local deployment

To deploy `conda-store` locally, run the following command:

```bash
docker compose up --build -d
```

On a fast machine, this should take about 10 seconds, assuming the docker images have been partially built before.

:::important
Most of the conda-store docker images are built/tested for amd64(x86-64). Notice the `architecture: amd64` within the `docker-compose.yaml` files.

There will be a performance impact when building and running on
arm architectures. Otherwise, this workflow has been shown to run and build on OSX.
:::

The following resources will be available on the deployment:

| Resource | Localhost port | username | password |
|----------|----------------|----------|----------|
| conda-store web server | [localhost:8080](http://localhost:8080)| `admin` | `password`|
| [JupyterHub](https://jupyter.org/hub) | [localhost:8000](http://localhost:8000) | any | `test` |
| [MinIO](https://min.io/) S3 |  [localhost:9000](http://localhost:9000) | `admin` | `password` |
| [PostgreSQL](https://www.postgresql.org/) (database: `conda-store`)| [localhost:5432](http://localhost:5432) | `admin` | `password` |
| [Redis](https://www.redis.com/) |  [localhost:6379](http://localhost:6379) | - | password |

### Make changes

If you make any changes to `conda-store-server`,
run the following to have those changes in the deployment:

```bash
docker compose down -v # not always necessary
docker compose up --build
```

To stop the deployment, run:

```bash
docker compose stop

# optional to remove the containers
docker compose rm -f
```

## Without Docker

1. Install [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html) before developing on conda-store.

2. Install the development dependencies and activate the environment:

   ```bash
   # replace this with environment-macos-dev.yaml or environment-windows-dev.yaml
   # if you are on Mac or Windows
   conda env create -f conda-store-server/environment-dev.yaml
   conda activate conda-store-server-dev
   ```

3. Running `conda-store` in `--standalone` mode launches celery as a
subprocess of the web server.

    ```bash
    python -m conda_store_server.server --standalone
   ```

1. Visit [localhost:8080](http://localhost:8080/) from your web browser.

## Run tests

### conda-store (client)

Linting and formatting checks can be performed via hatch.

```bash
$ cd conda-store
$ hatch env run -e dev lint
```

Running integration tests. These tests are stateful! So you will need
to clear the state if you have run the conda-store-server service on
docker.

```bash
$ cd conda-store
$ docker compose down -v # ensure you've cleared state
$ docker compose up --build
# wait until the conda-store-server is running check by visiting localhost:8080

$ pip install -e .
$ ./tests/unauthenticated-tests.sh
$ ./tests/authenticated-tests.sh
$ export CONDA_STORE_URL=http://localhost:8080/conda-store
$ export CONDA_STORE_AUTH=basic
$ export CONDA_STORE_USERNAME=username
$ export CONDA_STORE_PASSWORD=password
$ ./tests/shebang.sh
```

### conda-store-server

Linting and formatting checks can be performed via hatch.

```bash
$ cd conda-store-server
$ hatch env run -e dev lint
```

Checking that the package builds

```bash
$ cd conda-store-server
$ hatch build
```

Running unit tests

```bash
$ cd conda-store-server
$ pytest
```

Running integration tests. These tests are stateful! So you will need
to clear the state if you have run the conda-store-server service on
docker.

```bash
$ cd conda-store-server
$ docker-compose down -v # ensure you've cleared state
$ docker-compose up --build
# wait until the conda-store-server is running check by visiting localhos:8080
$ hatch env run -e dev playwright-test
$ hatch env run -e dev integration-test
```
