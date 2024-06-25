---
description: Contribute to conda-store's codebase
---

# Contribute code

:::warning
This page is in active development, content may be inaccurate and incomplete. If you encounter any content that needs improvement, please [create an issue](https://github.com/conda-incubator/conda-store/issues/new/choose) in our issue tracker.
:::

## `conda-store-core`

Before setting up your `conda-store-core` development environment you will need to have a local copy of the `conda-store` repository.

If you are a first-time contributor:

1. Go to [https://github.com/conda-incubator/conda-store/](https://github.com/conda-incubator/conda-store/) and click on the **Fork** button in the upper right corner to create your copy of the repository.
2. Clone the project to your local computer:

   ```bash
   git clone https://github.com/<your-GH-username>/conda-store/
   ```

Once you have a local copy of the `conda-store` repository, you can set up your development environment.
There are two main ways to set up your local environment for development:

- Using [Docker and docker-compose(recommended)](#docker-based-development---conda-store-core)
- Local development [without Docker](#local-development-without-docker---conda-store-core)

### Docker-based development - conda-store-core

Install the following dependencies before developing on `conda-store`.

- [Docker](https://docs.docker.com/engine/install/)
- [docker-compose](https://docs.docker.com/compose/install/)

To deploy `conda-store` run the following command:

```bash
docker-compose up --build -d
```

:::important
Many of the conda-store Docker images are built/tested for amd64(x86-64)
there will be a performance impact when building and running on
arm architectures.
Otherwise, this workflow has been shown to run and build on OSX.
**Notice** the `architecture: amd64` within the `docker-compose.yaml` files.
:::

After running the `docker-compose` command, the following resources will be available:

| Resource | Localhost port | username | password |
|----------|----------------|----------|----------|
| conda-store web server | [localhost:8080](http://localhost:8080)| `admin` | `password`|
| [JupyterHub](https://jupyter.org/hub) | [localhost:8000](http://localhost:8000) | any | `test` |
| [MinIO](https://min.io/) S3 |  [localhost:9000](http://localhost:9000) | `admin` | `password` |
| [PostgreSQL](https://www.postgresql.org/) (database: `conda-store`)| [localhost:5432](http://localhost:5432) | `admin` | `password` |
| [Redis](https://www.redis.com/) |  [localhost:6379](http://localhost:6379) | - | password |

On a fast machine, this deployment should only take 10 or so seconds
assuming the Docker images have been partially built before.

If you are making any changes to `conda-store-server` and would like to see
those changes in the deployment, run:

```shell
docker-compose down -v # not always necessary
docker-compose up --build
```

To stop the deployment, run:

```bash
docker-compose stop

# optional to remove the containers
docker-compose rm -f
```

### Local development without Docker - conda-store-core

You will need to install the following dependencies before developing on `conda-store`:

- [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)

1. Install the development dependencies and activate the environment:

   ```bash
   # from the root of the repository
   conda env create -f conda-store-server/environment-dev.yaml
   conda activate conda-store-server-dev
   ```

2. Install the package in editable mode:

   ```bash
   # from the root of the repository
   python -m pip install -e ./conda-store-server
   ```

3. Running `conda-store` in `--standalone` mode launches celery as a
subprocess of the web server.

    ```bash
    conda-store-server --standalone
    ```

4. You should now be able to access the `conda-store` server at [localhost:8080](http://localhost:8080/) from your web browser.

## `conda-store-ui`

Before setting up your `conda-store-ui` development environment you will need to have a local copy of the
`conda-store-ui` repository.

If you are a first-time contributor:

1. Go to [https://github.com/conda-incubator/conda-store-ui/](https://github.com/conda-incubator/conda-store-ui/) and click on the **Fork** button in the upper right corner to create your copy of the repository.
2. Clone the project to your local computer:

   ```bash
   git clone https://github.com/<your-GH-username>/conda-store-ui/
   ```

Once you have a local copy of the `conda-store` repository, you can set up your development environment.
There are two main ways to set up your local environment for development:

- Using [Docker and docker-compose(recommended)](#docker-based-development---conda-store-ui)
- Local development [without Docker](#local-development-without-docker---conda-store-ui)

### Pre-requisites

- [Node.js](https://nodejs.org/en/download/) >= 18
- [Yarn](https://classic.yarnpkg.com/lang/en/docs/)

### Docker-based development - conda-store-ui

Running conda-store-ui in Docker is the simplest way to set up your local development environment.

We use [docker-compose](https://docs.docker.com/compose/) to set up the infrastructure before starting,
you must ensure you have docker-compose installed.
If you need to install docker-compose, please see their [installation documentation](https://docs.docker.com/compose/install/).

1. After cloning the repository change to the project directory:

 ```bash
   # from your command line or terminal
   cd conda-store-ui
   ```

2. Copy `.env.example` to `.env`. All default settings should work, but if you want to test against a different version
   of `conda-store-server`, you can specify it in the `.env` file by setting the `CONDA_STORE_SERVER_VERSION` variable
   to the desired version.
3. Run `yarn run start:docker` to start the entire development stack.
4. Open your local browser and go to [http://localhost:8000](http://localhost:8000) so see conda-store-ui.
5. You can then log in using the default username of `username` and default password of `password`.

:::note

Hot reloading is enabled, so when you make changes to source files, your browser will automatically reload
and reflect the changes.

:::

### Local development without Docker - conda-store-ui

:::note

This setup still uses Docker for supporting services but runs conda-store-ui locally.

:::

#### Set up your environment

This project uses [conda](https://conda.io) for package management.
To set up conda, please see their [installation documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

1. After cloning the repository change to the project directory:

 ```bash
   # from your command line or terminal
   cd conda-store-ui
   ```

2. From the project root create and activate a new conda environment:

   ```bash
   conda env create -f environment_dev.yml
   conda activate cs-ui-dev-env
   ```

3. Install node dependencies:

   ```bash
   yarn install
   ```

#### Run the application

1. Run `yarn run start` and wait for the application to spin up.
Open your local browser and go to [http://localhost:8000](http://localhost:8000).
2. You can then log in using the default username of `username` and default password of `password`.

:::note

Hot reloading is enabled, so when you make changes to source files, your browser will reload and reflect the changes.
:::


<!-- TODO

## jupyterlab-conda-store

-->

## Workflows

### Changes to the API

The REST API is considered somewhat stable. If any changes are made to the API make sure the update the OpenAPI/Swagger
specification in `docs/_static/openapi.json`.
This may be downloaded from the `/docs` endpoint when running conda-store.
Ensure that the `c.CondaStoreServer.url_prefix` is set to `/` when generating the endpoints.

### Adding new dependencies to the libraries

### `conda-store-core`

Runtime-required dependencies should **only** be added to the corresponding `pyproject.toml` files:

- `conda-store-server/pyproject.toml`
- `conda-store/pyproject.toml`

Development dependencies should be added to both the `environment-dev.yaml` and `pyproject.toml` files.
Within the `pyproject.toml` file these should be added under the `[tool.hatch.envs.dev]` section.

This will ensure that conda-store distributions are properly built and tested with the correct dependencies.

:::important

The only exceptions to this runtime dependencies rules are `conda` and `constructor` which should be added to the
`environment-dev.yaml` file as they are only conda installable.

:::

### `conda-store-ui`

Dependencies should be added to the [`package.json`](https://github.com/conda-incubator/conda-store-ui/blob/main/package.json) file.

### Linting and formatting

We use pre-commit hooks to ensure that code is formatted and linted before being committed.
To install the pre-commit hooks, run:

```bash
pre-commit install --install-hooks
```

Now every time you commit, the pre-commit hooks will run and check your code.
We also use [pre-commit.ci](https://pre-commit.com/) to automatically run the pre-commit hooks on every Pull Request.
