---
sidebar_position: 5
description: Local development setup for conda-store-ui codebase
---

# Local setup for conda-store UI

To get started with conda-store-ui development, there are a couple of options. This guide will help you to set up your local development environment.

## Pre-requisites

No matter which option you choose, you must first complete the following steps.

1. [Install Docker Compose](https://docs.docker.com/compose/install/). We use [Docker Compose](https://docs.docker.com/compose/) to set up the infrastructure. So before starting, ensure that you have Docker Compose installed.
2. [Fork the conda-store-ui repository](https://github.com/conda-incubator/conda-store-ui/fork), then `git clone` it to your computer.
3. Copy `.env.example` to `.env`. All default settings should work, but if you want to test against a different version of conda-store-server, you can specify it in the `.env` file by setting the `CONDA_STORE_SERVER_VERSION` variable to the desired version.

## Basic local development (recommended)

Running conda-store-ui in Docker is the simplest way to set up your local development environment.

### Install the right version of Yarn

Yarn is a package manager for JavaScript dependencies. It requires that you [download and install Node.js](https://nodejs.org/en/download/package-manager). Once you have Node.js installed, you can follow the instructions to [install Yarn](https://yarnpkg.com/getting-started/install).

1. Change to the project root: `cd conda-store-ui`
2. Find out what version of Yarn is required: `cat package.json | grep packageManager`
3. Compare to the version of Yarn that you installed: `yarn --version`

### Run the UI web app in Docker container

1. Run `yarn install`. This will download or update the needed JavaScript dependencies into a directory named `node_modules/`. This directory will be exposed in the next step to the `conda-store-ui` Docker container for use at runtime by the Conda Store UI app.
2. Run `yarn run start:docker` to start the entire development stack. This step may take a few minutes the first time you run it.
3. Open your local browser and go to [http://localhost:8000](http://localhost:8000) to see conda-store-ui.
4. You can then log in using the default username of `username` and default password of `password`.

**Note:** Hot reloading is enabled, so when you make changes to source files, your browser will reload and reflect the changes.

## Advanced local development

For many Conda Store UI development tasks, the basic setup should work. But if you need to work extensively in the UI codebase, then you will probably want to run the conde-store-ui app locally rather than within a Docker container.

Note: this setup still uses Docker for supporting services (such as the database, server, worker, and cloud storage), but runs conda-store-ui locally.

### Set up your Conda environment

This project uses [Conda](https://conda.io) for package management. To set up Conda, please see their [installation documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

1. Change to the project root: `cd conda-store-ui`
2. From the project root, create the conda environment: `conda env create -f environment_dev.yml`

### Run the UI app locally

1. Activate the development environment: `conda activate cs-ui-dev-env`
2. Install/update JavaScript dependencies: `yarn install`
3. Run `yarn run start` and wait for the application to finish starting up
4. Open your local browser and go to [http://localhost:8000](http://localhost:8000) to see conda-store-ui.
5. You can then log in using the default username of `username` and default password of `password`.

**Note:** Hot reloading is enabled, so when you make changes to source files, your browser will reload and reflect the changes.

## Run the test suite

We currently use Jest in order to run unit tests.

```bash
yarn test     // find every test with the .test.[tsx|ts] extension
yarn report   // show coverage collected after running the first command in the browser
yarn report test/AddChannel.test.tsx     // run a single test instead of all
```
