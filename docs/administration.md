# Administration

## Resource Requirements

 - `conda-store-server` is simply a web server and should not require
   any specific resources. 1 GB of RAM and 1 cpu should be plenty.
 - `conda-store-worker` does the actual builds of the conda
   environments. Solving for conda environments can take a lot of
   memory in some circumstances. So make sure to allocate at least 4
   GB of RAM to the worker along with at least one cpu.

## Performance

There are several parts of conda-store to consider for performance. We
have tried to list them in order of performance impact that may be
seen. 

### Worker Storage

When conda-store builds a given environment it has to locally install
the environment in the directory specified in the traitlets
configuration `CondaStore.store_directroy`. Conda environments consist
of many small files that are hardlinked. This means that the
`store_directory` is limited to the number of
[IOPS](https://en.wikipedia.org/wiki/IOPS) the directory can
perform. Many cloud providers have high performance storage
options. These include:

If you do not need to mount the environments via NFS into the
containers we highly recommend not using NFS and using traditional
block storage. Not only is it significantly cheaper but the IOPs
performance will be better as well.

If you want to mount the environments in containers or running VMs NFS
may be a good option for you. With NFS many cloud providers provide a
high performance filesystem option at a significant premium in
cost. Example of these include [gcp
filestore](https://cloud.google.com/filestore/docs/performance#expected_performance),
[aws efs](https://aws.amazon.com/efs/features/), and [azure
files](https://docs.microsoft.com/en-us/azure/storage/files/understanding-billing#provisioning-method). Choosing
an nfs storage option with bad IOPs will yield long environment
install times.

### Network Speed

Conda while it does it's best to cache packages will have to reach out
to download the `repodata.json` along with the packages as well. Thus
network speeds may be important. Typically cloud environments have
plenty fast Internet.

### S3 Storage

All build artifacts from conda-store are stored in object storage that
behaves S3 like. S3 traditionally has great performance if you use the
cloud provider implementation.

### Celery Broker

Celery is used for sending out tasks for building and deleting
environment and builds. By default a sqlalchemy database backed
backend is used. Databases like postgres are quite performant and
unlikely to be a bottleneck. However if issues arise celery can use
many [message queue based databases as a
broker](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/index.html).

## Configuration

conda-store is configured via
[traitlets](https://traitlets.readthedocs.io/en/stable/). Originally
this configuration was done via command line options but as the
options grew this seems untenable. conda-store server and worker can
be launched via configuration easily.

```shell
conda-store-server --config <path-to-conda-store-config.py>
```

```shell
conda-store-worker --config <path-to-conda-store-config.py>
```

Below we outline the options for conda-store.

### conda_store_server.app.CondaStore

`CondaStore.storage_class` configures the storage backend to use for
storing build artifacts from
conda-store. [S3](https://en.wikipedia.org/wiki/Amazon_S3) storage is
the default. File based storage is also supported but not nearly as
well tested.

`CondaStore.store_directory` is the directory used for conda-store to
build the environments. 

`CondaStore.environment_directory` is the directory that conda-store
will created symlinks for the environments that are built in the
`store_directory`.

`CondaStore.conda_command` is the `command` to use for creation of
conda environments. Currently `mamba` is the default which will
usually result in lower peak memory usage and faster builds.

`CondaStore.conda_channel_alias` is the url to prepend to all
shorthand conda channels that do not specify a url. The default is
`https://conda.anaconda.org`.

`CondaStore.conda_allowed_channels` is a list of conda channels that
are allowed (currently not enforced). This also tells conda-store
which channels to prefetch the channel repodata from. The default is
`https://repo.anaconda.com/pkgs/main` and `conda-forge`.

`CondaStore.database_url` is the url string for connecting to the
database. Behind the scenes [sqlalchemy](https://www.sqlalchemy.org/)
is used for the connection so [consult their
docs](https://docs.sqlalchemy.org/en/14/core/engines.html) for
connecting to your specific database. Conda-Store will automatically
create the tables if they do not already exist.

`CondaStore.celery_broker_url` is the broker use to use for
celery. Celery supports a [wide range of
brokers](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/index.html)
each with different guarantees. By default the sqlalchemy based broker
is used. While this is production ready it is not the ideal broker it
has worked well in practice. The url must be provided in a format that
celery understands.

`CondaStore.build_artifacts` is the list of artifacts for conda-store
to build. By default it is all the artifacts that conda-store is
capable of building. These are the
[lockfile](https://github.com/conda-incubator/conda-lock),
[yaml](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually),
[conda pack](https://conda.github.io/conda-pack/), and
[docker](https://github.com/conda-incubator/conda-docker). Currently
the `lockfile` one is ignored since it is always created upon build.

`CondaStore.build_artifacts_kept_on_deletion` is a list of artifacts
to keep after a given build is deleted. Often an administrator will
want to keep around the logs etc. of a build and the conda solve for
the given build.

`CondaStore.celery_results_backend` is the backend to use for storing
all results from celery task execution. Conda-store currently does not
leverage the backend results but it may be needed for future work
using celery. The backend defaults to using the sqlalchemy
backend. This is a great production choise. Please consult the [celery
docs on
backend](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/index.html).

`CondaStore.default_namespace` is the default namespace for
conda-store to use. All environments are built behind a given
namespace.

`CondaStore.default_uid` is the the uid (user id) to assign to all
files and directories in a given built environment. This setting is
useful if you want to protect environments from modification from
certain users and groups.

`CondaStore.default_gid` is the the gid (group id) to assign to all
files and directories in a given built environment. This setting is
useful if you want to protect environments from modification from
certain users and groups.

`CondaStore.default_permissions` is the filesystem permissions to
assign to all files and directories in a given built environment. This
setting is useful if you want to protect environments from
modification from certain users and groups.

`CondaStore.default_docker_base_image` is the base image to use for
docker builds of conda environments. This package at a minimum should
have the [following packages
installed](https://docs.anaconda.com/anaconda/install/linux/). Often
times for non-graphic and non-gpu environments glibc is enough. Hence
the default docker image `frolvlad/alpine-glibc:latest`.

### conda_store_server.storage.S3Storage

Conda-Store uses [minio-py](https://github.com/minio/minio-py) as a
client to connect to S3 "like" object stores.

`S3Storage.internal_endpoint` is the internal endpoint for conda-store
reaching out to s3 bucket. This is the url that conda-store use for
get/set s3 blobs. For AWS S3 use the endpoint `s3.amazonaws.com`.

`S3Storage.external_endpoint` is the external endpoint for users to
reach out to s3 bucket to fetch presigned urls. This is the url that
users use for fetching s3 blobs. For AWS S3 use the endpoint
`s3.amazonaws.com`.

`S3Storage.access_key` is the access key for S3 bucket.

`S3Storage.secret_key` is the secret key for S3 bucket.

`S3Storage.region` is the region to use for connecting to the S3
bucket. The default is `us-east-1`.

`S3Storage.bucket_name` is the bucket name to use for connecting to
the S3 bucket.

`S3Storage.secure` boolean to indicate if connecting via `http`
(False) or `https` (True).

`S3Storage.credentials` provider to use to get credentials for s3
access. see examples
https://github.com/minio/minio-py/tree/master/examples and
documentation
https://github.com/minio/minio-py/blob/master/docs/API.md#1-constructor. An
example of this could be to use `minio.credentials.IamAwsProvider` to
get S3 credentials via IAM.

`S3Storage.credentials_args` arguments to pass for creation of
credentials class.

`S3Storage.credentials_kwargs` keyword arguments to pass for creation
of credentials class.

### conda_store_server.storage.LocalStorage

`LocalStorage.storage_path` is the base directory to use for storing
build artifacts.

`LocalStorage.storage_url` is the base url for serving of build
artifacts. This url assumes that the base will be a static server
serving `LocalStorage.storage_path`.

### conda_store_server.server.auth.AuthenticationBackend

`AuthenticationBackend.secret` is the symetric secret to use for
encrypting tokens.

`AuthenticationBackend.jwt_algorithm` is the algorithm for encrypting
the json web tokens.

### conda_store_server.server.auth.AuthorizationBackend

`AuthorizationBackend.role_mappings` is a dictionary that maps `roles`
to application `permissions`. There are three default roles at the
moment `viewer`, `developer`, and `admin`.

`AuthorizationBackend.unauthenticated_role_bindings` are the role
bindings that an unauthenticated user assumes.

`AuthorizationBackend.authenticated_role_bindings` are the base role
bindings that an authenticated user assumes.

### conda_store_server.server.auth.Authentication

`Authentication.cookie_name` is the name for the browser cookie used
to authenticate users.

`Authentication.authentication_backend` is the class to use for
authentication logic. The default is `AuthenticationBackend` and will
likely not need to change.

`Authentication.authorization_backend` is the class to use for
authentication logic. The default is `AuthorizationBackend` and will
likely not need to change.

`Authentication.login_html` is the html to display for a given user as
the login form.

### conda_store_server.server.auth.DummyAuthentication

Has all the configuration settings of `Authetication`. This class is
modeled after the [jupyterhub DummyAuthentication
class](https://github.com/jupyterhub/jupyterhub/blob/9f3663769e96d2e4f665fd6ef485c101704c4645/jupyterhub/auth.py#L1142).

`DummyAuthentication.password` sets a global password for all users to
login with. Effectively a static password. This rarely if ever should
be used outside of testing.

### conda_store_server.server.auth.GenericOAuthAuthentication

A provider-agnostic OAuth authentication provider. Configure
endpoints, secrets and other parameters to enable any OAuth-compatible
platform. This class is modeled after the [oauthenticator oauth
classes](https://github.com/jupyterhub/oauthenticator). All
configuration settings of `Authentication` are available.

`GenericOAuthAuthentication.access_token_url` is the URL used to
request an access token once app has been authorized.

`GenericOAuthAuthentication.authorizie_url` is the URL used to request
authorization to OAuth provider.

`GenericOAuthAuthentication.client_id` is the unique string that
identifies the app against the OAuth provider.

`GenericOAuthAuthentication.client_secret` is the secret string used
to authenticate the app against the OAuth provider.

`GenericOauthAuthentication.access_scope` is the permissions that will
be requested to oauth provider. This is space separated list of
scopes. Generally only one scope is requested.

`GenericOauthAuthentication.user_data_url` is the API endpoint for
OAuth provider that returns a JSON dict with user data after the user
has successfully authenticated.

`GenericOauthAuthentication.user_data_key` is the key in the payload
returned by `user_data_url` endpoint that provides the `username`.

### conda_store_server.server.auth.GithubOAuthAuthentication

Inherits from `Authentication` and `GenericOAuthAuthentication` so
should be fully configurable from those options.

`GithubOAuthAuthentication.github_url` is the url for github. Default
is `https://github.com`.

`GithubOAuthAuthentication.github_api` is the rest api url for
github. Default is `https://api.github.com`.

### conda_store_server.server.auth.JupyterHubOAuthAuthentication

Inherits from `Authentication` and `GenericOAuthAuthentication` so
should be fully configurable from those options.

`GithubOAuthAuthentication.jupyterhub_url` is the url for connecting
to JupyterHub. The URL should not include the `/hub/`.

### conda_store_server.server.app.CondaStoreServer

`CondaStoreServer.log_level` is the level for all server
logging. Default is `INFO`. Common options are `DEBUG`, `INFO`,
`WARNING`, and `ERROR`.

`CondaStoreServer.enable_ui` a boolean on whether to expose the UI
endpoints. Default True.

`CondaStoreServer.enable_api` a boolean on whether to expose the API
endpoints. Default True.

`CondaStoreServer.enable_registry` a boolean on whether to expose the
registry endpoints. Default True.

`CondaStoreServer.enable_metrics` a boolean on whether to expose the
metrics endpoints. Default True.

`CondaStoreServer.address` is the address for the server to bind
to. The default is all ip addresses `0.0.0.0`.

`CondaStoreServer.port` is the port for conda store server to
use. Default is `5000`.

`CondaStoreServer.registry_external_url` is the external hostname and
port to access docker registry cannot contain `http://` or `https://`.

`CondaStoreServer.url_prefix` is the prefix URL (subdirectory) for the
entire application. All but the registry routes obey this. This is due
to the docker registry api specification not supporting url prefixes.

`CondaStoreServer.authentication_class` is the authentication class
for the web server to use. Default is `DummyAuthentication`.

`CondaStoreServer.secret_key` is a secret key needed for some
authentication methods, session storage, etc. TODO: remove at some
point since also used in `AuthenticationBackend`.

`CondaStoreServer.max_page_size` is maximum number of items to return
in a single UI page or api response.

### conda_store_server.worker.app.CondaStoreWorker

`CondaStoreWorker.log_level` is the level for all server
logging. Default is `INFO`. Common options are `DEBUG`, `INFO`,
`WARNING`, and `ERROR`.

`CondaStoreWorker.watch_paths` is a list of paths for conda store to
watch for changes to directories of `environment.yaml` files or a
single filename to watch.

## Frequently Asked Questions

### Conda-store fails to build conda environment and worker is spontaneously killed (9 SIGKILL)

The following error most likely indicates that you have not allocated
enough memory to `conda-store-workers` for solving and building the
given environment. Solve this by increasing the memory allocated to
the container.

```shell
Process 'ForkPoolWorker-31' pid:90 exited with 'signal 9 (SIGKILL)'

Task handler raised error: WorkerLostError('Worker exited prematurely: signal 9 (SIGKILL) Job: 348.')

Traceback (most recent call last):
File "/opt/conda/envs/conda-store-server/lib/python3.9/site-packages/billiard/pool.py", line 1265, in mark_as_worker_lost

    raise WorkerLostError(

billiard.exceptions.WorkerLostError: Worker exited prematurely: signal 9 (SIGKILL) Job: 348.
```
