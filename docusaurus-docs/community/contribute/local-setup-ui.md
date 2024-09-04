---
sidebar_position: 5
description: Local development setup for conda-store-ui codebase
---

# Local setup for conda-store UI

To get started with conda-store-ui development, there are a couple of options. This guide will help you to set up your local development environment.

## Pre-requisites

No matter which option you choose, you must first complete the following steps.

1. [Install Docker Compose](https://docs.docker.com/compose/install/). We use [Docker Compose](https://docs.docker.com/compose/) to set up the infrastructure. So before starting, ensure that you have Docker Compose installed.
2. [Fork the conda-store-ui repository](https://github.com/conda-incubator/conda-store-ui/fork)
3. `git clone` the fork to your computer.

## Basic Option (recommended): Run the UI in Docker

For basic local development on the UI, running conda-store-ui in Docker is the simplest way to get started.

1. Change your working directory to the project root: `cd conda-store-ui`
2. Optional. Set environment variables. Copy `.env.example` to `.env`. All default settings should work, but if you want to test against a different version of conda-store-server, you can specify it in the `.env` file by setting the `CONDA_STORE_SERVER_VERSION` variable to the desired version. If you skip this step, it will be done automatically for you.
3. Run `docker compose --profile local-dev up --build` to start the entire development stack. This step may take a few minutes the first time you run it.
4. Open your local browser and go to [http://localhost:8000](http://localhost:8000) to see conda-store-ui.
5. You can then log in using the default username of `username` and default password of `password`.

**Note:** Hot reloading is enabled, so when you make changes to source files (i.e., files under the conda-store-ui/src/ directory), your browser will reload and reflect the changes.

## Advanced Option: Run the UI locally (with the rest of the stack in Docker)

For more advanced development on conda-store-ui, the first option might not be sufficient. If you need to work extensively in the UI codebase, then you will probably want to run the UI web app locally rather than within a Docker container.

Note: this setup still uses Docker to run the rest of the Conda Store stack. That means that the Conda Store database, server, worker, and storage services will all run in Docker containers. But the frontend web app (conda-store-ui) will run locally (not in a Docker container) with this setup.

### Set up your Conda environment

This project uses [Conda](https://conda.io) for package management. To set up Conda, please see their [installation documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

1. Change to the project root: `cd conda-store-ui`
2. From the project root, create the conda environment: `conda env create -f environment_dev.yml`

### Run conda-store-ui locally (and the rest of the stack in Docker)

Tip: Make sure are in the project root: `cd conda-store-ui`

1. Activate the development environment: `conda activate cs-ui-dev-env`
2. Set environment variables. Copy `.env.example` to `.env`. All default settings should work, but if you want to test against a different version of conda-store-server, you can specify it in the `.env` file by setting the `CONDA_STORE_SERVER_VERSION` variable to the desired version.
3. Install/update JavaScript dependencies: `yarn install`
4. Run `yarn run start` and wait for the application to finish starting up. This command will run a local dev server for the UI app and run the other Conda Store services in Docker.
5. Open your local browser and go to [http://localhost:8000](http://localhost:8000) to see conda-store-ui.
6. You can then log in using the default username of `username` and default password of `password`.

**Note:** Hot reloading is enabled, so when you make changes to source files, your browser will reload and reflect the changes.

## Run the test suite

We currently use Jest in order to run unit tests.

```bash
yarn test     // find every test with the .test.[tsx|ts] extension
yarn report   // show coverage collected after running the first command in the browser
yarn report test/AddChannel.test.tsx     // run a single test instead of all
```
