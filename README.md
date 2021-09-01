# Conda Store

[![Documentation Status](https://readthedocs.org/projects/conda-store/badge/?version=latest)](https://conda-store.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/conda-store-server?label=pypi|conda-store-server)](https://pypi.org/project/conda-store-server/)
[![PyPI](https://img.shields.io/pypi/v/conda-store?label=pypi|conda-store)](https://anaconda.org/conda-forge/conda-store)
[![Conda](https://img.shields.io/conda/vn/conda-forge/conda-store-server?color=green&label=conda-forge%7Cconda-store-server)](https://anaconda.org/conda-forge/conda-store-server)
[![Conda](https://img.shields.io/conda/vn/conda-forge/conda-store?color=green&label=conda-forge%7Cconda-store)](https://anaconda.org/conda-forge/conda-store)

![conda store UI](docs/_static/images/conda-store-authenticated.png)

End users think in terms of environments not packages. The core
philosophy of conda-store is to serve identical conda environments in
as many ways as possible. Conda Store controls the environment
lifecycle: management, builds, and serving of environments.

It **manages** conda environments by:
 - watching specific files or directories for changes in environment filename specifications 
 - provides a REST api for managing environments (which a jupyterlab plugin is being actively developed for)
 - provides a command line utility for interacting with conda-store `conda-store env [create, list]`
 - provides a web ui to take advantage of many of conda-store's advanced capabilities

It **builds** conda specifications in a scalable manner using `N`
workers communicating via Celery to keep track of queued
environment builds.

It **serves** conda environments via a filesystem, lockfiles,
tarballs, and soon a docker registry. Tarballs and docker images can
carry a lot of bandwidth which is why conda-store integrates
optionally with `s3` to actually serve the blobs.

## Documentation

All documentation can be found on Read the Docs including how to develop
and contribute to the
project. [conda-store.readthedocs.io](https://conda-store.readthedocs.io).

## Terminology

 - A `namespace` is a way of scoping environments

 - An `environment` is a `namespace` and `name` pointing to a particular `build`

 - A `specification` is a conda environment `yaml` declaration with fields `name`,
   `channels`, and `dependencies` as detailed
   [here](https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html)
   
 - A `build` is a build (`conda env create -f <specification>`) of a
   particular `specification` at a point in time for a given `namespace`

This design has several advantages:
 - `environments` can be "rolled back" to a given `build` - not necessarily the latest
 - because each `environment` update is a new separate build the
   environment can be archived and uniquely identified

![conda-store terminology](docs/_static/images/conda-store-terminology.png)

## Philosophy

We mentioned above that `conda-store` was influenced by
[nix](https://nixos.org/). While conda is not as pure as nix (when it
comes to reproducible builds) we can achieve close to the same results
with many of the great benefits. Motivation
from this work came from the following projects in no particular
order: [lorri](https://github.com/target/lorri), [nix layered docker
images](https://grahamc.com/blog/nix-and-layered-docker-images),
[https://nixos.org/](nix), [nixery](https://nixery.dev/). 

1. specifications are idempotent, created once, and never updated
   (this means there is no `conda install` or `conda env update`). In
   fact there is only one conda command `conda env create -f
   <specification>`.
2. specifications are named
   `<sha256-hash-of-spec>-<environment-name>`, ensuring every conda
   environment is unique.
3. a conda environment e.g. `<environment-name>` is symlinked to a
   specific conda specification
   `<sha256-hash-of-spec>-<environment-name>`.

The benefits of this approach are versioning of environments, heavy
caching, and rollbacks to previous environment states. 

## License

Conda-Store is [BSD-3 LICENSED](./LICENSE)

## Contributing

Our [documentation has all the information needed for
contributing](https://conda-store.readthedocs.io/en/latest/contributing.html). We
welcome all contributions.
