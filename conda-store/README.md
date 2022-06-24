# Conda Store

[![Documentation Status](https://readthedocs.org/projects/conda-store/badge/?version=latest)](https://conda-store.readthedocs.io/en/latest/?badge=latest)

A client library for interacting with a Conda-Store server. See the
[documentation](https://conda-store.readthedocs.io/en/latest/) for
more information. The client library provides a CLI for interacting
with conda-store.

```shell
$ conda_store --help
Usage: conda_store [OPTIONS] COMMAND [ARGS]...

Options:
  --conda-store-url TEXT     Conda-Store base url including prefix
  --auth [none|token|basic]  Conda-Store authentication to use
  --no-verify-ssl            Disable tls verification on API requests
  --help                     Show this message and exit.

Commands:
  download  Download artifacts for given build
  info      Get current permissions and default namespace
  run       Execute given environment specified as a URI with COMMAND
```
