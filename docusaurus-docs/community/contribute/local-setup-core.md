---
sidebar_position: 4
description: Local development setup for conda-store
---

# Local setup for conda-store (core)

There are two main ways to set up your local environment and conda-store services (web UI, API server, database, etc.) for development:

- Using [Docker and Docker compose](#docker-setup-recommended): This is the recommended approach for working on `conda-store-server` library.
- Using [standalone mode](#standalone-setup): This approach avoids using docker and starts the conda-store services as one process

:::important
You need a [local copy of the `conda-store` repository](community/contribute/contribute-code#setup-for-local-development) for the development setup.
:::

## Docker setup (recommended) 🐳

### Pre-requisites

Install the following dependencies before developing on conda-store:

- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/install/)

### Local deployment

To **deploy `conda-store` locally**, run the following command:

```bash
docker compose up --build -d
```

On a fast machine, this should take about 10 seconds, assuming the docker images have been partially built before.

:::note
Most of the conda-store docker images are built/tested for amd64(x86-64). Notice the `architecture: amd64` within the `docker-compose.yaml` files.

There will be a performance impact when building and running on
ARM architectures. Otherwise, this workflow has been shown to run and build on OSX.
:::

The following resources will be available on the deployment:

| Resource | Localhost port | username | password |
|----------|----------------|----------|----------|
| **conda-store web server (UI)** ✨| [localhost:8080](http://localhost:8080)| `admin` | `password`|
| [MinIO](https://min.io/) S3 |  [localhost:9000](http://localhost:9000) | `admin` | `password` |
| [PostgreSQL](https://www.postgresql.org/) (database: `conda-store`)| [localhost:5432](http://localhost:5432) | `admin` | `password` |
| [Redis](https://www.redis.com/) |  [localhost:6379](http://localhost:6379) | - | password |

If you **make any changes** to `conda-store-server`,
run the following to have those changes in the deployment:

```bash
docker compose down -v
docker compose up --build
```

To **stop the deployment**, run:

```bash
docker compose stop
```

Optionally, to remove the containers, run:

```bash
docker compose rm -f
```

## Standalone setup 💻

### Pre-requisites

You need **conda** for this setup, you can install it with the instructions in the [documentation][conda-install].

### Development environment

Create a conda environment with the development dependencies, and activate the environment:

```bash
conda env create -f conda-store-server/environment-dev.yaml
conda activate conda-store-server-dev
```

To install the `conda-store-server` package in editable (development) mode, run the following from the root of the repository:

```bash
python -m pip install -e ./conda-store-server
```

### Start conda-store in standalone mode

Running `conda-store` in `--standalone` mode launches celery as a
subprocess of the web server.

```bash
python -m conda_store_server.server --standalone
```

Visit [localhost:8080](http://localhost:8080/) from your web browser to access the conda-store web UI. ✨

## Run the test suite ✅

You can run the codebase tests locally to verify your changes before submitting a pull request.
You need [Docker Compose](#pre-requisites) as well as the [conda development environment](#development-environment) to run the complete set of tests.

### conda-store-server

#### Lint and format

Run the linting and formatting checks with hatch:

```bash
cd conda-store-server
hatch env run -e dev lint
```

#### Package build

Check that the package builds:

```bash
cd conda-store-server
hatch build
```

#### Unit tests

Run the unit tests with pytest:

```bash
cd conda-store-server
pytest
```

#### Integration tests

These tests are stateful, so clear the state if you previously ran the conda-store-server service on Docker:

```bash
cd conda-store-server
docker-compose down -v # ensure you've cleared state
docker-compose up --build
```

Wait until the conda-store-server is running check by visiting [localhost:8080](http://localhost:8080).

Run the tests with hatch:

```bash
hatch env run -e dev playwright-test
hatch env run -e dev integration-test
```

<!-- External links -->

[conda-install]: https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html
