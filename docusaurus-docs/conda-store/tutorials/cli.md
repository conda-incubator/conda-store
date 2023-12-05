---
description: Use the CLI
---

# Use the CLI

:::warning
This page is in active development, content may be inaccurate.
:::

The conda-store client can be easily installed via pip or conda.

```shell
pip install conda-store

# OR

conda install -c conda-forge conda-store
```

The base CLI is inspired by tools such as
[conda](https://docs.conda.io/en/latest/),
[kubectl](https://kubernetes.io/docs/reference/kubectl/), and
[docker](https://docs.docker.com/get-docker/). The base commands are
`download`, `info`, `list`, `run`, `wait`.

```shell
$ conda-store --help
Usage: conda-store [OPTIONS] COMMAND [ARGS]...

Options:
  --conda-store-url TEXT     conda-store base url including prefix
  --auth [none|token|basic]  conda-store authentication to use
  --no-verify-ssl            Disable tls verification on API requests
  --help                     Show this message and exit.

Commands:
  download  Download artifacts for given build
  info      Get current permissions and default namespace
  list
  run       Execute given environment specified as a URI with COMMAND
  solve     Remotely solve given environment.yaml
  wait      Wait for given URI to complete or fail building
```

### `conda-store run`

One of the motivating features of the `conda-store` cli is that you
can directly execute conda-store environments that exist remotely.

```shell
conda-store run devops/datascience -- python -m "print(1)"
```

### `conda-store solve`

conda-store is capable to remote solves of environment files. If
requested conda-store can perform intelligent solves with caching.

### `conda-store download`

<!-- TODO -->

### `conda-store info`

<!-- TODO -->

### `conda-store wait`

<!-- TODO -->

### `conda-store list [namespace|environment|build]`

<!-- TODO -->

<!-- TODO: Include conda-store-server CLI, like standalone -->
