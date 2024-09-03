---
sidebar_position: 5
description: Local development setup for conda-store-ui codebase
---

# Local setup for conda-store UI

To get started with conda-store-ui development, there are a couple of options. This guide will help you to set up your local development environment.

## Pre-requisites

We use [Docker Compose](https://docs.docker.com/compose/) to set up the infrastructure before starting ensure that you have Docker compose installed. If you need to install docker-compose, please see their [installation documentation](https://docs.docker.com/compose/install/)

1. Fork and clone the [conda-store-ui](https://github.com/conda-incubator/conda-store-ui.git) repository.
2. Copy `.env.example` to `.env`. All default settings should work, but if you want to test against a different version of conda-store-server, you can specify it in the `.env` file by setting the `CONDA_STORE_SERVER_VERSION` variable to the desired version

## Docker (Recommended)

Once you have a [local copy of the `conda-store` repository](community/contribute/contribute-code#setup-for-local-development)

Running conda-store-ui in Docker is the simplest way to set up your local development environment.

1. Run `yarn run start:docker` to start the entire development stack.
Open your local browser and go to [http://localhost:8000](http://localhost:8000) so see conda-store-ui.
3. You can then log in using the default username of `username` and default password of `password`.

**Note:** Hot reloading is enabled, so when you make changes to source files, your browser will reload and reflect the changes.

## Without Docker

This setup still uses Docker for supporting services but runs conda-store-ui locally.

### Set up your environment

This project uses [Conda](https://conda.io) for package management. To set up Conda, please see their [installation documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).
1. Change to the project root ` cd conda-store-ui`
2. From the project root create the conda environment `conda env create -f environment_dev.yml`
3. Activate the development environment `conda activate cs-ui-dev-env`
4. Install yarn dependencies `yarn install`

### Run the application

1. Run `yarn run start` and wait for the application to finish starting up
Open your local browser and go to [http://localhost:8000](http://localhost:8000) so see conda-store-ui.
3. You can then log in using the default username of `username` and default password of `password`.

**Note:** Hot reloading is enabled, so when you make changes to source files, your browser will reload and reflect the changes.

## Run the test suite

We currently use jest in order to run unit tests.

```bash
yarn test     // find every test with the .test.[tsx|ts] extension
yarn report   // show coverage collected after running the first command in the browser
yarn report test/AddChannel.test.tsx     // run a single test instead of all
```
