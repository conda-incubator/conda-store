---
description: Contribute to conda-store
---

# Run test suite

:::warning
This page is in active development, content may be inaccurate and incomplete.
:::

## conda-store (client)

Linting and formatting checks can be performed via hatch.

```shell
$ cd conda-store
$ hatch env run -e dev lint
```

Running integration tests. These tests are stateful! So you will need
to clear the state if you have run the conda-store-server service on
docker.

```shell
$ cd conda-store
$ docker-compose down -v # ensure you've cleared state
$ docker-compose up --build
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

## conda-store-server

Linting and formatting checks can be performed via hatch.

```shell
$ cd conda-store-server
$ hatch env run -e dev lint
```

Checking that package builds

```shell
$ cd conda-store-server
$ hatch build
```

Running unit tests

```shell
$ cd conda-store-server
$ pytest
```

Running integration tests. These tests are stateful! So you will need
to clear the state if you have run the conda-store-server service on
docker.

```shell
$ cd conda-store-server
$ docker-compose down -v # ensure you've cleared state
$ docker-compose up --build
# wait until the conda-store-server is running check by visiting localhos:8080
$ hatch env run -e dev playwright-test
$ hatch env run -e dev integration-test
```
