# conda-store

[![Documentation Status](https://readthedocs.org/projects/conda-store/badge/?version=latest)](https://conda-store.readthedocs.io/en/latest/?badge=latest)

A client library for interacting with a conda-store server. See the
[documentation](https://conda-store.readthedocs.io/en/latest/) for
more information. The client library provides a CLI for interacting
with conda-store.

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
