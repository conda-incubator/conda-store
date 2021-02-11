# Architecture

Conda Store was designed with the idea of scalable enterprise
management of reproducible conda environments.

![Conda Store architecture diagram](_static/images/conda-store-architecture.png)

## Workers and Server

Conda Store can be broken into two components. The worker(s) which
have the following responsibilities:
 - build Conda environments from Conda `environment.yaml` specifications
 - build Conda pack archives
 - build Conda docker images
 - remove Conda builds

All of the worker logic is in `conda_store/build.py` at the moment but
will be soon refactored into a task directory.
 
The web server has several responsibilities:
 - serve a ui for interacting with conda environments
 - serve a rest api for managing conda environments
 - serve a programmatic docker registry for interesting docker-conda abilities

The web server under `conda_store.server` is broken into several components:
 - ui :: `conda_store/server/views/ui.py`
 - api :: `conda_store/server/views/api.py`
 - registry :: `conda_store/server/views/registry.py`

Both the worker and server need a connection to the database and s3
server. The s3 server is used to store all build artifacts e.g. logs,
docker layers, and the conda pack tarball. The postgresql database is
used for managing the tasks for the conda-store workers along with
powering the conda-store web server ui, api, and docker registry.

## Terminology

 - environment :: a pointer to a build of a given specification
 - specification :: a Conda environment.yaml file
 - build :: a attempt of `conda env install -f environment.yaml`

In order to understand why we have the complicated terminology for an
environment it helps to understand how conda builds a given
environment. 

## Reproducibility of Conda 

```yaml
name: example
channels:
  - defaults
  - conda-forge
dependencies:
  - python >=3.7
```

Suppose we have the given `environment.yaml` file. How does conda
perform a build?

1. Conda downloads `channeldata.json` from each of the channels which
   list the available architectures.
   
2. Conda then downloads `repodata.json` for each of the architectures
   it is interested in (specifically your compute architecture along
   with noarch). The `repodata.json` has fields like package name,
   version, and dependencies.

You may notice that the channels listed above do not have urls. This
is because in general you can add
`https://conda.anaconda.org/<channel-name>` to a non-url channel. 

3. Conda then performs a solve to determine the exact version/sha of each
   package that it will download

4. The specific packages are downloaded

5. Conda does magic to fix the path prefixes of the install

There are two spots that introduce issues to reproducibility. The
first issue is tracking when an `environment.yaml` file has
changes. This can be easily tracked by taking a sha256 of the file
. This is what conda-store does but sorts the dependencies to make
sure it has a way of not triggering a rebuild if the order of two
packages changes in the dependencies list. In step (2) `repodata.json`
is updated regularly. When conda solves for a user's environment it
tries to use the latest version of each package. Since `repodata.json`
could be updated the next minute the same solve for the same
`environment.yaml` file can result in different solves.

