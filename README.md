# Conda Store

Conda Store controls the environment lifecycle: management, builds, and
serves. It is opinionated and highly motivated by a heavy nix
user. 

It **manages** conda environments by watching specific files or
directories for changes in environment specifications and provides a
REST api for managing environments

It **builds** conda specifications in a scalable manner

It **serves** conda environments via a filesystem, tarballs, and as
docker containers.

We want end users to think in terms of environments and not packages.

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

