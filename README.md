# Conda Store

[![Documentation Status](https://readthedocs.org/projects/conda-store/badge/?version=latest)](https://conda-store.readthedocs.io/en/latest/?badge=latest)

![PyPI](https://img.shields.io/pypi/v/conda-store)

End users think in terms of environments not packages. The core
philosophy of conda-store is to serve identical conda environments in
as many ways as possible. Conda Store controls the environment
lifecycle: management, builds, and serving of environments.

It **manages** conda environments by:
 - watching specific files or directories for changes in environment filename specifications 
 - provides a REST api for managing environments (which a jupyterlab plugin is being actively developed for)
 - provides a command line utility for interacting with conda-store `conda-store env [create, list]`
 - provides a web ui to take advantage of many of conda-stores advanced capabilities

It **builds** conda specifications in a scalable manner using `N`
workers communicating with a database to keep track of queued up
environment builds.

It **serves** conda environments via a filesystem, lockfiles,
tarballs, and soon a docker registry. Tarballs and docker images can
carry a lot of bandwidth which is why conda-store integrates
optionally with `s3` to actually serve the blobs.

## Terminology

 - An environment is a `name` associated with an environment `specification`.

 - A specification is a conda `yaml` declaration with fields `name`,
   `channels`, and `dependencies` detailed
   [here](https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html)
   
 - For each specification conda-build attempts to build the
   specification. Upon failure conda-store reschedules the build `N`
   times with exponential backoff.

## Philosophy

We mentioned above that `conda-store` was influenced by
[nix](https://nixos.org/). While conda is not as pure as nix (when it
comes to reproducible builds) we can achieve close to the same results
with many of the great benefits that nix users achieve. Motivation
from this work came from the following projects in no particular
order: [lorri](https://github.com/target/lorri), [nix layered docker
images](https://grahamc.com/blog/nix-and-layered-docker-images),
[https://nixos.org/](nix), [nixery](https://nixery.dev/). You will see
bits of each in this work.

1. specifications are idempotent, created once, and never updated
   (this means there is no `conda install` or `conda env update`). In
   fact there is only one conda command `conda env create -f
   <specification>`.
2. specifications are named
   `<sha256-hash-of-spec>-<environment-name>`. Ensuring every conda
   environment is unique.
3. conda environments e.g. `<environment-name>` is symlinked to a
   specific conda specification
   `<sha256-hash-of-spec>-<environment-name>`.

The benefits of this approach is versioning of environments, heavy
caching, and rollbacks to previous environment states. 

# Development

```shell
docker-compose up --build
```

In order for logs and artifacts to be downloaded properly you will
need to set dns host `minio` -> `localhost`. The easiest way to do
this is via `/etc/hosts`

```shell
...
minio localhost
...
```
