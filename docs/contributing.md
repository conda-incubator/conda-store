# Contributing

## Naming

When refering to `conda-store` it should always be written all
lowercase with a dash in between. `conda-store` should also be
lowercase when beginning a sentence.

## Development

Significant effort has been put into simplifying the development and
deployment process of `conda-store`. There is a docker based
development workflow along with a non-containerized workflow if you
are using Linux.

### Containerized development

Install the following dependencies before developing on conda-store.

- [docker](https://docs.docker.com/engine/install/)
- [docker-compose](https://docs.docker.com/compose/install/)

To deploy `conda-store` run the following command

```shell
docker-compose up --build -d
```

:::{important}
Many of the conda-store docker images are built/tested for amd64(x86-64)
there will be a performance impact when building and running on
arm architectures. Otherwise this workflow has been shown to run and build on OSX.
Notice the `architecture: amd64` whithin the docker-compose.yaml files.
:::

:::{warning}
If you're developing on a Mac and run into issues that complain about `tcp 0.0.0.0:5000: bind: address already in use` you might need to deactivate the `Airplay Receiver` service from the `Sharing` section in Control Center.
Have a look at this [discussion on Apple.com](https://developer.apple.com/forums/thread/682332)
for more details.
:::

The following resources will be available:

- conda-store web server running at [http://localhost:5000](http://localhost:5000)
- [MinIO](https://min.io/) s3 running at [http://localhost:9000](http://localhost:9000) with username `admin` and password `password`
- [PostgreSQL](https://www.postgresql.org/) running at [localhost:5432](http://localhost:5432) with username `admin` and password `password` database `conda-store`
- [Redis](https://www.redis.com/) running at [localhost:6379](http://localhost:6379) with password `password`
- [JupyterHub](https://jupyter.org/hub) running at [http://localhost:8000](http://localhost:8000) with any username and password `test`

On a fast machine this deployment should only take 10 or so seconds
assuming the docker images have been partially built before. If you
are making and changes to conda-store-server and would like to see
those changes in the deployment. Run.

```shell
docker-compose down -v # not always necessary
docker-compose up --build
```

### Linux development

Install the following dependencies before developing on conda-store.

- [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)

Install the development dependencies and activate the environment.

```shell
# replace this with environment-macos-dev.yaml or environment-windows-dev.yaml
# if you are on Mac or Windows
conda env create -f conda-store-server/environment-dev.yaml
conda activate conda-store-server-dev
```

Running `conda-store`. `--standalone` mode launched celery as a
subprocess of the web server. Run

```
python -m conda_store_server.server --standalone
```

Then visit [localhost:5000](http://localhost:5000/).

### Changes to API

The REST API is considered somewhat stable. If any changes are made to
the API make sure the update the OpenAPI/Swagger specification in
`docs/_static/openapi.json`. This may be downloaded from the `/docs`
endpoint when running conda-store. Ensure that the
`c.CondaStoreServer.url_prefix` is set to `/` when generating the
endpoints.

## Documentation

Install the following dependencies before contributing to the
documentation.

 - [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)

To build the documentation install the development environment via
Conda.

```shell
# replace this with environment-macos-dev.yaml or environment-windows-dev.yaml
# if you are on Mac or Windows
conda env create -f conda-store-server/environment-dev.yaml
conda activate conda-store-server-dev
````

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

### Testing

The `conda-store` repository is two packages.

- `conda-store-server/` which is the worker + web server responsible for the `conda-store` service
- `conda-store/` is the client which interacts with the service

#### conda-store

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
# wait until the conda-store-server is running check by visiting localhost:5000

$ pip install -e .
$ ./tests/unauthenticated-tests.sh
$ ./tests/authenticated-tests.sh
$ export CONDA_STORE_URL=http://localhost:5000/conda-store
$ export CONDA_STORE_AUTH=basic
$ export CONDA_STORE_USERNAME=username
$ export CONDA_STORE_PASSWORD=password
$ ./tests/shebang.sh
```

#### conda-store-server

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
# wait until the conda-store-server is running check by visiting localhos:5000
$ hatch env run -e dev playwright-test
$ hatch env run -e dev integration-test
```

## Release process

Choose the `<version>` number. It should follow [Semantic
Versioning](https://semver.org/) and the established pattern of
`v<x>.<y>.<z>`.

Ensure that `CHANGELOG.md` is up to date with all the changes since
the last release following the template provided within the markdown
file.

All docker images within `docker/kubernetes` should be updated to the
release version. `spec.template.spec.containers[0].image` is the path
within the YAML files.

Update the version number in `conda-store-server/conda_store_server/__init__.py` and
`conda-store/conda_store/__init__.py` to reflect the release version.

Once those changes have been made make a commit titled `bump to
version <version>`.

Finally create a [new release within the GitHub
interface](https://github.com/conda-incubator/conda-store/releases/new). Do
this instead of a git TAG since you can include release notes on the
repository. The Release should be titled `Release <version> -
<month>/<day>/<year>` with the description being the changelog
markdown for the particular release.

Once you have create a release the GitHub actions with the build the
release and make it available on [PyPi](https://pypi.org/),
[Conda](https://anaconda.org/), and
[DockerHub](https://hub.docker.com/).

After the PyPi release a release on
[Conda-Forge](https://conda-forge.org/) and it located at
[conda-forge/conda-store-feedstock](https://github.com/conda-forge/conda-store-feedstock). A
PR must be created that updates to the released version
`<version>`.

conda-store has two PyPi packages `conda-store-server` and `conda-store`.

- update `recipies/meta.yaml` with the new version `{% set version = "<version>" %}`
- update `recipies/meta.yaml` with the appropriate sha256 for each
  package. The sha256 can be found at
  `https://pypi.org/project/conda-store/#files` by clicking the
  `view` button.

Once the PR has been created ensure that you request a `rerender` of
the feedstock with the following comment `@conda-forge-admin please
rerender`. An example of this can be found in [PR
#2](https://github.com/conda-forge/conda-store-feedstock/pull/2)

## Architecture

conda-store was designed with the idea of scalable enterprise
management of reproducible Conda environments.

![conda-store architecture diagram](_static/images/conda-store-architecture.png)

### Configuration

[Traitlets](https://traitlets.readthedocs.io/en/stable/) is used for
all configuration of conda-store. In the beginning command line
options were used but eventually we learned that there were too many
options for the user. Traitlets provides a python configuration file
that you can use to configure values of the applications. It is used
for both the server and worker. See
[`tests/assets/conda_store_config.py`](https://github.com/conda-incubator/conda-store/blob/main/tests/assets/conda_store_config.py)
for a full example.

### Workers and server

conda-store can be broken into two components. The workers which have
the following responsibilities:

- build Conda environments from Conda `environment.yaml` specifications
- build Conda pack archives
- build Conda docker images
- remove Conda builds
- modify symlinks to point current environment to given build
- generally any tasks that can take an unbounded amount of time

All of the worker logic is in `conda_store_server/build.py` and
`conda_store_server/worker/*.py`. Celery is used for managing tasks so
you will see the celery tasks defined in
`conda_store_server/worker/tasks.py` which in turn usually call built
in `CondaStore` functions in `conda_store_server/app.py` or
`conda_store_server/build.py`.

The web server has several responsibilities:

- serve a UI for interacting with Conda environments
- serve a REST API for managing Conda environments
- serve a programmatic Docker registry for interesting docker-conda abilities

The web server is based on
[FastAPI](https://fastapi.tiangolo.com/). Originally Flask was chosen
due to it being battle tested and that conda-store is not doing any
special things with the web server. However, over time the ability for
robust input and output guarantees from the endpoints along with auto
documentation made FastAPI appealing. The backend web app is defined
in `conda_store_server.server.app`. There are several components to
the server:

- UI :: `conda_store_server/server/views/ui.py`
- REST API :: `conda_store_server/server/views/api.py`
- registry :: `conda_store_server/server/views/registry.py`

Both the worker and server need a connection to a SQLAchemy compatible
database, Redis, and S3 compatible object storage. The S3 server is
used to store all build artifacts for example logs, docker layers, and
the [Conda-Pack](https://conda.github.io/conda-pack/) tarball. The
PostgreSQL database is used for storing all states on environments and
builds along with powering the conda-store web server UI, REST API,
and Docker registry. Redis is used for keeping track of task state and
results along with enabling locks and realtime streaming of logs.

### Terminology

![conda-store terminology](_static/images/conda-store-terminology.png)

`conda_environment = f(open("environment.yaml"), datatime.utcnow())`

- namespace :: a way of providing scopes between environments. This
  prevents Joe's environment named `data-science` from colliding from
  Alice's environment name `data-science`.
- environment :: a pointer to a current build of a given specification
- specification :: a [Conda environment.yaml file](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually)
- build :: a attempt of `conda env install -f environment.yaml` at a
  given point in time

In order to understand why we have the complicated terminology for an
environment it helps to understand how Conda builds a given
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

Suppose we have the given `environment.yaml` file. How does Conda
perform a build?

1. Conda downloads `channeldata.json` from each of the channels which
   list the available architectures.

2. Conda then downloads `repodata.json` for each of the architectures
   it is interested in (specifically your compute architecture along
   with noarch). The `repodata.json` has fields like package name,
   version, and dependencies.

You may notice that the channels listed above do not have a url. This
is because in general you can add
`https://conda.anaconda.org/<channel-name>` to a non-url channel.

3. Conda then performs a solve to determine the exact version and
   sha256 of each package that it will download

4. The specific packages are downloaded

5. Conda does magic to fix the path prefixes of the install

There are two spots that introduce issues to reproducibility. The
first issue is tracking when an `environment.yaml` file has
changes. This can be easily tracked by taking a sha256 of the file
. This is what conda-store does but sorts the dependencies to make
sure it has a way of not triggering a rebuild if the order of two
packages changes in the dependencies list. In step (2) `repodata.json`
is updated regularly. When Conda solves for a user's environment it
tries to use the latest version of each package. Since `repodata.json`
could be updated the next minute the same solve for the same
`environment.yaml` file can result in different solves.

### Authentication Model

Authentication was modeled after JupyterHub for implementation. There
is a base class `conda_store_server.server.auth.Authenticaiton`. If
you are extending and using a form of OAuth2 use the
`conda_store_server.server.auth.GenericOAuthAuthentication`. Similar
to JupyterHub all configuration is modified via
[Traitlets](https://traitlets.readthedocs.io/en/stable/). Below shows
an example of setting us OAuth2 via JupyterHub for conda-store.

```python
c.CondaStoreServer.authentication_class = JupyterHubOAuthAuthentication
c.JupyterHubOAuthAuthentication.jupyterhub_url = "http://jupyterhub:8000"
c.JupyterHubOAuthAuthentication.client_id = "service-this-is-a-jupyterhub-client"
c.JupyterHubOAuthAuthentication.client_secret = "this-is-a-jupyterhub-secret"
```

Once a user is authenticated a cookie or [JSON Web
Token](https://jwt.io/) is created to store the user credentials to
ensure that conda-store is as stateless as possible. At this current
point in time conda-store does not differentiate between a service and
user. Similar to JupyterHub
`conda_store_server.server.auth.Authentication` has an `authenticate`
method. This method is the primary way to customize authentication. It
is responsible for checking that the user credentials to login are
correct as well as returning a dictionary following the schema
`conda_store_server.schema.AuthenticationToken`. This stores a
`primary_namespace` for a given authenticated service or user. In
addition a dictionary of `<namespace>/<name>` map to a set of
roles. See the Authorization model to better understand the key to set
of roles meaning.

### Authorization Model

conda-store implements role based authorization to supports a flexible
authorization model. A user or service is either authenticated or
not. There are a set of default permissions assigned to authenticated
and unauthenticated users via Traitlets. These can all be modified in
the configuration. These roles are inherited based on the
authentication status of the user or service. To support hierarchies
we map a key such as `default/*` to a set of roles. The `/` separates
the `<namespace>` from the `<name>` and `*` signifies match any (zero
or more) characters. This was chosen to support rich authorization
models while also being easy and efficient to implement in a
database. `*` are supported anywhere in the `key` such as
`*n*viron*/n*me`. Configure the following Traitlets to modify the
inherited permissions for authenticated and unauthenticated users.

```python
c.RBACAuthorizationBackend.unauthenticated_role_bindings = {
    "default/*": {"viewer"},
}

c.RBACAuthorizationBackend.authenticated_role_bindings = {
    "default/*": {"viewer"},
    "filesystem/*": {"viewer"},
}
```

Once we have collected the role mappings that a given user has we then
map `roles` to sets of permissions. Currently there are only a few
permissions but conda-store is capable of adapting in the future.

```python
class Permissions(enum.Enum):
    ENVIRONMENT_CREATE = "build::create"
    ENVIRONMENT_READ = "build::read"
    ENVIRONMENT_UPDATE = "build::update"
    ENVIRONMENT_DELETE = "build::delete"
```

The role name to permission is configured via a single trait shown
below `c.RBACAuthorizationBackend.role_mappings`.

```python
c.RBACAuthorizationBackend.role_mappings = {
    "viewer": {
        Permissions.ENVIRONMENT_READ
    },
    "developer": {
        Permissions.ENVIRONMENT_CREATE,
        Permissions.ENVIRONMENT_READ,
        Permissions.ENVIRONMENT_UPDATE,
    },
    "admin": {
        Permissions.ENVIRONMENT_CREATE,
        Permissions.ENVIRONMENT_READ,
        Permissions.ENVIRONMENT_UPDATE,
        Permissions.ENVIRONMENT_DELETE,
    },
}
```

Lets go through a few examples to make this more concrete and assume
the default configuration of conda-store.

> Suppose we have an unauthenticated user trying to view the
> environment `quansight/datascience`.

First since the user is unauthenticated they inherit the default role
mappings.

```python
{
    "default/*": {"viewer"},
}
```

We go through each role mapping and try to match the expression
`default/*` to `quansight/datascience`. In this case this does not
match and thus for the given environment `quansight/datascience` the
unauthenticated user has no roles. This user does not have any roles
for the given environment but if they did we would iterate through all
roles and combine the permissions. The next example will show this. So
for this example the user has permissions `{}` in the given
environment. The action of viewing a given environment requires
`build::read` which the unauthenticated user does not have.

> Suppose we have an unauthenticated user trying to delete the
> environment `default/web-dev`.

First since the user is unauthenticated they inherit the default role
mappings.

```
{
    "default/*": {"viewer"},
}
```

We go through each role mapping and try to match the expression
`default/*` to `default/web-dev`. In this case this does match and
thus for the given environment `default/web-dev` the unauthenticated
user has a set of roles `{viewer}`. For each role we map the role to
permissions. We get `{build::read}`. The delete environment action
requires `build::delete` permissions and thus the user is not
authenticated to perform the action.

> Suppose we have an authenticated user trying to delete the
> environment `default/web-dev`.

First since the user is authenticated they inherit the default role
mappings.

```python
{
    "default/*": {"viewer"},
    "filesystem/*": {"viewer"},
}
```

In addition to the default role bindings the user was authenticated
via the `authenticate` method and has the following bindings added.

```python
{
    "*/*": {"admin"}
}
```

In total the user has the following bindings.

```python
{
    "default/*": {"viewer"},
    "filesystem/*": {"viewer"},
    "*/*": {"admin"},
}
```

Following the same process as before we iterate through each binding
if it matches we add the given roles. For this example we get
`{viewer, admin}`. Next we iterate through each role and map it to
permissions and we get the following `{build::create, build::read,
build::update, build::delete}`. The delete environment action requires
`build::delete` permissions which the user has thus the action is
permitted.

## Database

### Model

At a high level the database model can be described in the image
bellow.

![high level diagram](_static/images/conda-store-database-architecture.png)

Important things to note about the relationship:

- An `environment` exists within a given `namespace` and always has a current `build`
- A `build` belongs to a particular `environment` and has associated `condapackage` and `buildartfacts`
- A `buildartifact` is a way for the database to keep track of
  external resources for example s3 artifacts, filesystem directories,
  etc
- A `condapackage` is a representation of a given Conda package which belongs to a given `condachannel`
- A `specification` is the environment.yaml using in `conda env create -f <environment.yaml>`

The following will generate the database model shown bellow. It was
generated from the `examples/docker` example. You'll see in the
command that we are excluding several tables. These tables are managed
by [celery](https://docs.celeryproject.org/en/stable/).

```shell
pip install eralchemy  # not available on conda-forge
eralchemy -i "postgresql+psycopg2://admin:password@localhost:5432/conda-store"  \
    -x celery_tasksetmeta celery_taskmeta kombu_queue kombu_message alembic_version \
    -o output.png
```

![entity relationship diagram](_static/images/conda-store-entity-relationship-diagram.png)

### Migrations

conda-store relies on [SQLAlchemy](https://www.sqlalchemy.org/) for ORM mapping, and on [Alembic](https://alembic.sqlalchemy.org/en/latest/) for DB migrations.

The procedure to modify the database is the following :

- First, modify [the ORM Model](https://github.com/conda-incubator/conda-store/blob/main/conda-store-server/conda_store_server/orm.py) according to the changes you want to make
- edit the file `conda-store-server/alembic.ini` and replace the value for entry `sqlalchemy.url` to match the connection URL of your database.

For example (when postgres was started via docker-compose):
```
script_location = alembic
sqlalchemy.url = postgresql+psycopg2://postgres:password@localhost:5432/conda-store
```

- in your command line, run the following :

```sh
cd conda-store-server/conda_store_server
alembic revision --autogenerate -m "description of your changes"
```

- You should have a new file in `conda-store-server/conda_store_server/alembic/versions/` . **Review it thoroughly**. It contains the [`alembic` operations](https://alembic.sqlalchemy.org/en/latest/ops.html) (`op`) to actually modify the database, either when upgrading (`upgrade` function) or downgrading (`downgrade`)

- You can migrate your data within these `upgrade`/`downgrade` functions, for example :

```python
from alembic import op

# revision identifiers, used by Alembic.
revision = 'abcdef01234567'
down_revision = '987654321f0edc'
branch_labels = None
depends_on = None

def upgrade():

    # operations to modify the database structure
    # ...
    op.create_table(
        'new_table',
        Column('id', INTEGER, primary_key=True),
        Column('field1', VARCHAR(50), nullable=False),
        Column('field2', INTEGER),
        Column('timestamp', TIMESTAMP, server_default=func.now())
    )
    # ...

    op.execute('''INSERT INTO new_table (field1, field2)
                  SELECT field1, field2
                  FROM old_table''')

    # other operations to modify the database structure
    # ...


def downgrade():

    op.drop_table('new_table')

```

- Once you're sure about the changes generated, you can apply them by running :

```sh
alembic upgrade head
```

- Check your database : your changes should be reflected. If not, refer to [Alembic's documentation](https://alembic.sqlalchemy.org/en/latest/).
