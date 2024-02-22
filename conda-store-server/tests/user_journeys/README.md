# User Journey Tests

This repository contains user journey tests for the API. User journey tests
are end-to-end tests that simulate real user scenarios to ensure the API
functions correctly in different scenarios.

These tests will use the high-privileged token to create a randomly-named
namespace (using a UUID) to prevent conflicts with existing namespaces. At the
end of the test, it will delete any environments created and then delete the
namespace.

## Prerequisites

These tests are blackbox tests and need a running server to test against. This
can be a local conda-store instance started using docker compose, or a remote
instance. You will need the base url of the server and a token for an admin
user to run these tests.

## Setup

### Local setup

To run locally using docker compose all you need to do is start conda-store.

From the project base, run `docker compose up`.

### Remote setup

To run these tests against a remote server, you need to set 2 environment
variables:

1. `CONDA_STORE_BASE_URL` - this is the base url of your conda-store-server.

   For example, if you access your conda-store-server at `https://example.com`,
   you would run `export CONDA_STORE_BASE_URL='https://example.com'`.

   **Do not include the `/conda-store/` suffix.**

   Do include the port if needed.
   For example: `export CONDA_STORE_BASE_URL='http://localhost:8080'`.

2. `CONDA_STORE_TOKEN` - this should be the token of an admin user.

    This token will let the tests create the tokens, permissions, namespaces,
    and environments needed for these tests to run successfully.

    To generate a token, while logged in as a high-privileged user, go to
    `https://<your-conda-store-url>/conda-store/admin/user/` and click on
    `Create token`.

    Copy that token value and export it:
    `export CONDA_STORE_TOKEN='my_token_value'`.

## Running the tests

To run the tests, run `pytest -m user_journey` from the `conda-store-server`
directory.

## Current scenarios tested

* An admin user can create a simple environment in a shared namespace and, once
    the environment is built, can delete the environment.

## Planned scenarios to be implemented

* An admin can create a complex environment in a shared namespace and, once the
    environment is built, can delete the environment

* A developer can create a simple environment in a shared namespace and, once
    the environment is built, can delete the environment

* A developer can create a complex environment in a shared namespace and, once
    the environment is built, can delete the environment

* A developer can create an environment in a shared namespace and, once the
    environment is built, can modify the environment, then can mark the first
    build as active

* A developer can create a simple environment in a shared namespace and, once
    the environment is built, can get the lockfile for the environment

* A developer can create a failing environment in a shared namespace and, once
    the environment has failed, can get the logs for the failed build.
