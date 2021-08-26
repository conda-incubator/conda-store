# Contributing

## Development

The following are needed for development

 - [docker](https://docs.docker.com/engine/install/)
 - [docker-compose](https://docs.docker.com/compose/install/)

To deploy `conda-store` run the following command

```shell
docker-compose up --build
```

The following resources will be available:
  - conda-store web server running at http://localhost:5000
  - minio s3 running at http://localhost:9000 with username `admin` and password `password`
  - postgres running at localhost:5432 with username `admin` and password `password` database `conda-store`
  - jupyterhub running at http://localhost:8000 with any username and password `test`

On a fast machine this deployment should only take 10 or so seconds
assuming the docker images have been partially built before. If you
are making and changes to conda-store-server and would like to see
those changes in the deployment. Run.

```shell
docker-compose down  # not always necissary
docker-compose up --build
```

## Documentation

The following are needed for development

 - [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

To build the documentation install the development environment via
conda.

```shell
conda env create -f conda-store-server/environment-dev.yaml
conda activate conda-store-server-dev
```

Then go in the documentation directory `docs` and build the
documentation.

```shell
cd docs
sphinx-build -b html . _build
```

Then open the documentation via your favorite web browser.

```shell
firefox _build/index.html
```

The documentation has been primarily written in markdown as to make it
easier to contribute to the documentation.

## REST API

### Status

 - `GET /api/v1/` :: get status of conda-store

### Namespace

 - `GET /api/v1/namespace/` :: list namespaces

### Environments

 - `GET /api/v1/environment/` :: list environments

 - `GET /api/v1/environment/<namespace>/<name>/` :: get environment

 - `PUT /api/v1/environment/<namespace>/<name>/` :: update environment to given build id
 
### Specifications

 - `POST /api/v1/environment/` :: create given environment
 
### Builds

 - `GET /api/v1/build/` :: list builds

 - `GET /api/v1/build/<build_id>/` :: get build

 - `PUT /api/v1/build/<build_id>/` :: trigger new build of given build specification

 - `DELETE /api/v1/build/<build_id>/` :: delete given build

 - `GET /api/v1/build/<build_id>/logs/` :: get build logs

### Packages

 - `GET /api/v1/channel/` :: list channels

### Packages

 - `GET /api/v1/package/` :: list packages

## Architecture

Conda Store was designed with the idea of scalable enterprise
management of reproducible conda environments.

![Conda Store architecture diagram](_static/images/conda-store-architecture-simple.png)

### Configuration

[Traitlets](https://traitlets.readthedocs.io/en/stable/) is used for
all configuration of conda-store. In the beginning command line
options were used but eventually we learned that there were too many
options for the user. Traitlets provides a python configuration file
that you can use to configure values of the applications. It is used
for both the server and worker. See
[tests/assets/conda_store_config.py](https://github.com/Quansight/conda-store/blob/main/tests/assets/conda_store_config.py)
for a full example.

### Workers and Server

Conda Store can be broken into two components. The worker(s) which
have the following responsibilities:
 - build Conda environments from Conda `environment.yaml` specifications
 - build Conda pack archives
 - build Conda docker images
 - remove Conda builds
 - modify symlinks to point current environment to given build

All of the worker logic is in `conda_store_server/build.py` and
`conda_store_server/worker/*.py`. Celery is used for managing tasks so
you will see the celery tasks defined in
`conda_store_server/worker/tasks.py` which in turn usually call built
in `CondaStore` functions in `conda_store_server/app.py` or
`conda_store_server/build.py`.
 
The web server has several responsibilities:
 - serve a ui for interacting with conda environments
 - serve a rest api for managing conda environments
 - serve a programmatic docker registry for interesting docker-conda abilities

The web server is based on
[Flask](https://flask.palletsprojects.com/en/2.0.x/). Flask was chosen
due to it being battle tested and that conda-store is not doing any
special things with the web server. The flask app is defined in
`conda_store_server.server.app`. There are several components to the server:
 - ui :: `conda_store_server/server/views/ui.py`
 - api :: `conda_store_server/server/views/api.py`
 - registry :: `conda_store_server/server/views/registry.py`

Both the worker and server need a connection to the database and s3
server. The s3 server is used to store all build artifacts e.g. logs,
docker layers, and the conda pack tarball. The postgresql database is
used for managing the tasks for the conda-store workers along with
powering the conda-store web server ui, api, and docker
registry. Optionally a broker can be used for tasks that is not a
database e.g. a message queue similar to rabbitmq, kafka, etc. It is
not believed that a full blown message queue will help conda-store with
performance.

### Terminology

![Conda Store terminology](_static/images/conda-store-terminology.png)

`conda_environment = f(open("environment.yaml"), datatime.utcnow())` 

 - namespace :: a way of providing scopes between environments. This
   prevents joe's environment named `data-science` from colliding from
   Alice's environment name `data-science`.
 - environment :: a pointer to a current build of a given specification
 - specification :: a [Conda environment.yaml file](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually)
 - build :: a attempt of `conda env install -f environment.yaml` at a
   given point in time

In order to understand why we have the complicated terminology for an
environment it helps to understand how conda builds a given
environment. 

### Reproducibility of Conda 

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

