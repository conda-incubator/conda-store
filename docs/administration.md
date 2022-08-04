# Administration

## Resource Requirements

 - `conda-store-server` is simply a web server and should not require
   any specific resources. 1 GB of RAM and 1 CPU should be plenty.
 - `conda-store-worker` does the actual builds of the Conda
   environments. Solving for Conda environments can take a lot of
   memory in some circumstances. So make sure to allocate at least 4
   GB of RAM to the worker along with at least one CPU.

## Performance

There are several parts of conda-store to consider for performance. We
have tried to list them in order of performance impact that may be
seen. 

### Worker Storage

When conda-store builds a given environment it has to locally install
the environment in the directory specified in the
[Traitlets](https://traitlets.readthedocs.io/en/stable/using_traitlets.html)
configuration `CondaStore.store_directroy`. Conda environments consist
of many hardlinks to small files. This means that the
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
cost. Example of these include [GCP
Filestore](https://cloud.google.com/filestore/docs/performance#expected_performance),
[AWS EFS](https://aws.amazon.com/efs/features/), and [Azure
files](https://docs.microsoft.com/en-us/azure/storage/files/understanding-billing#provisioning-method). Choosing
an nfs storage option with low IOPS will result in long environment
install times.

### Network Speed

While Conda does its best to cache packages, it will have to reach out
to download the `repodata.json` along with the packages as well. Thus
network speeds may be important. Typically cloud environments have
plenty fast Internet.

### S3 Storage

All build artifacts from conda-store are stored in object storage that
behaves S3 like. S3 traditionally has great performance if you use the
cloud provider implementation.

## Configuration

conda-store is configured via
[Traitlets](https://traitlets.readthedocs.io/en/stable/). Originally
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

### `conda_store_server.app.CondaStore`

`CondaStore.storage_class` configures the storage backend to use for
storing build artifacts from
conda-store. [S3](https://en.wikipedia.org/wiki/Amazon_S3) storage is
the default. File based storage is also supported but not nearly as
well tested.

`CondaStore.store_directory` is the directory used for conda-store to
build the environments. 

`CondaStore.build_directory` template used to form the directory for
storing Conda environment builds. Available keys: `store_directory`,
`namespace`, `name`. The default will put all built environments in the
same namespace within the same directory.

`CondaStore.environment_directory` template used to form the directory
for symlinking Conda environment builds. Available keys:
store_directory, namespace, name. The default will put all
environments in the same namespace within the same directory.

`CondaStore.validate_specification` callable function taking
`conda_store` and `specification` as input arguments to apply for
validating and modifying a given specification. If there are
validation issues with the environment ValueError with message will be
raised.

`CondaStore.conda_command` is the `command` to use for creation of
Conda environments. Currently `mamba` is the default which will
usually result in lower peak memory usage and faster builds.

`CondaStore.conda_channel_alias` is the url to prepend to all
shorthand Conda channels that do not specify a url. The default is
`https://conda.anaconda.org`.

`CondaStore.conda_platforms` are the platforms to download package
repodata.json from. By default includes current architecture and
`noarch`.

`CondaStore.conda_default_channels` is a list of Conda channels that
are by default added if channels within the specification is empty.

`CondaStore.conda_allowed_channels` is a list of Conda channels that
are allowed. This also tells conda-store which channels to prefetch
the channel `repodata` and `channeldata` from. The default is `main`
and `conda-forge`. If `conda_allowed_channels` is an empty list all
Channels are accepted by users.

`CondaStore.conda_default_packages` is a list of Conda packages that
are included by default if none are specified within the specification
dependencies.

`CondaStore.conda_required_packages` is a list of Conda packages that
are required upon validation of the specification dependencies. This
will not auto add the packages but instead throw an error that they
are missing.

`CondaStore.conda_included_packages` is a list of Conda packages that
if not specified within the specification dependencies will be auto
added.

`CondaStore.pypi_default_packages` is a list of PyPi packages that
are included by default if none are specified within the specification
dependencies.

`CondaStore.pypi_required_packages` is a list of PyPi packages that
are required upon validation of the specification dependencies. This
will not auto add the packages but instead throw an error that they
are missing.

`CondaStore.pypi_included_packages` is a list of PyPi packages that
if not specified within the specification dependencies will be auto
added.

`CondaStore.database_url` is the url string for connecting to the
database. Behind the scenes [SQLAlchemy](https://www.sqlalchemy.org/)
is used for the connection so [consult their
docs](https://docs.sqlalchemy.org/en/14/core/engines.html) for
connecting to your specific database. conda-store will automatically
create the tables if they do not already exist.

`CondaStore.redis_url` is a required argument to a running Redis
instance. This became a dependency as of release `0.4.1` due to the
massive advantages of features that conda-store can provide with this
dependency. See
[documentation](https://github.com/redis/redis-py/#connecting-to-redis)
for proper specification. This url is used by default for the Celery
broker and results backend.

`CondaStore.celery_broker_url` is the broker use to use for
celery. Celery supports a [wide range of
brokers](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/index.html)
each with different guarantees. By default the Redis based broker is
used. It is production ready and has worked well in practice. The url
must be provided in a format that celery understands. The default
value is `CondaStore.redis_url`.

`CondaStore.build_artifacts` is the list of artifacts for conda-store
to build. By default it is all the artifacts that conda-store is
capable of building. These are the
[lockfile](https://github.com/conda-incubator/conda-lock),
[YAML](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually),
[Conda-Pack](https://conda.github.io/conda-pack/), and
[Docker](https://github.com/conda-incubator/conda-docker). Currently
the `lockfile` one is ignored since it is always created upon build.

`CondaStore.build_artifacts_kept_on_deletion` is a list of artifacts
to keep after a given build is deleted. Often an administrator will
want to keep around the logs etc. of a build and the Conda solve for
the given build.

`CondaStore.celery_results_backend` is the backend to use for storing
all results from celery task execution. conda-store currently does not
leverage the backend results but it may be needed for future work
using celery. The backend defaults to using the Redis backend. This
choice works great in production. Please consult the [celery docs on
backend](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/index.html).

`CondaStore.default_namespace` is the default namespace for
conda-store to use. All environments are built behind a given
namespace.

`CondaStore.filesystem_namespace` is the namespace to use for
environments picked up via `CondaStoreWorker.watch_paths` on the
filesystem.

`CondaStore.default_uid` is the uid (user id) to assign to all
files and directories in a given built environment. This setting is
useful if you want to protect environments from modification from
certain users and groups.

`CondaStore.default_gid` is the gid (group id) to assign to all
files and directories in a given built environment. This setting is
useful if you want to protect environments from modification from
certain users and groups.

`CondaStore.default_permissions` is the filesystem permissions to
assign to all files and directories in a given built environment. This
setting is useful if you want to protect environments from
modification from certain users and groups.

`CondaStore.default_docker_base_image` is the base image to use for
docker builds of Conda environments. This package at a minimum should
have the [following packages
installed](https://docs.anaconda.com/anaconda/install/linux/). Often
times for non-graphic and non-gpu environments glibc is enough. Hence
the default docker image `library/debian:sid-slim`.

`CondaStore.serialize_builds` no longer build Conda environment in
parallel. This is due to an issue in Conda/Mamba that when downloading
files in two concurrent builds the downloads/extraction can
overlap. This is a bug in Conda/Mamba that needs to be fixed. Default
is True until this bug is fixed.

### `conda_store_server.storage.S3Storage`

conda-store uses [minio-py](https://github.com/minio/minio-py) as a
client to connect to S3 "like" object stores.

`S3Storage.internal_endpoint` is the internal endpoint for conda-store
reaching out to s3 bucket. This is the url that conda-store use for
get/set s3 blobs. For AWS S3 use the endpoint `s3.amazonaws.com`.

`S3Storage.external_endpoint` is the external s3 endpoint for users to
reach out to in the presigned url. This is the url that users use
for fetching s3 blobs. For AWS S3 use the endpoint `s3.amazonaws.com`.

`S3Storage.access_key` is the access key for S3 bucket.

`S3Storage.secret_key` is the secret key for S3 bucket.

`S3Storage.region` is the region to use for connecting to the S3
bucket. The default is `us-east-1`.

`S3Storage.bucket_name` is the bucket name to use for connecting to
the S3 bucket.

`S3Storage.internal_secure` Boolean to indicate if connecting via
`http` (False) or `https` (True) internally. The internal connection
is the url that will be exclusively used by conda-store and not shared
with users.

`S3Storage.external_secure` Boolean to indicate if connecting via
`http` (False) or `https` (True) internally. The external connection
is the url that will be served to users of conda-store.

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

### `conda_store_server.storage.LocalStorage`

`LocalStorage.storage_path` is the base directory to use for storing
build artifacts.

`LocalStorage.storage_url` is the base url for serving of build
artifacts. This url assumes that the base will be a static server
serving `LocalStorage.storage_path`.

### `conda_store_server.server.auth.AuthenticationBackend`

`AuthenticationBackend.secret` is the symmetric secret to use for
encrypting tokens.

`AuthenticationBackend.jwt_algorithm` is the algorithm for encrypting
the JSON Web Tokens.

`AuthenticationBackend.predefined_tokens` is a set of tokens with
predefined permission. This is useful for setting up service accounts
in a similar manner to how things are done with jupyterhub. Format for
the values is a dictionary with keys being the tokens and values being
the `schema.AuthenticaitonToken` all fields are optional.

### `conda_store_server.server.auth.AuthorizationBackend`

`AuthorizationBackend.role_mappings` is a dictionary that maps `roles`
to application `permissions`. There are three default roles at the
moment `viewer`, `developer`, and `admin`.

`AuthorizationBackend.unauthenticated_role_bindings` are the role
bindings that an unauthenticated user assumes.

`AuthorizationBackend.authenticated_role_bindings` are the base role
bindings that an authenticated user assumes.

### `conda_store_server.server.auth.Authentication`

`Authentication.cookie_name` is the name for the browser cookie used
to authenticate users.

`Authentication.authentication_backend` is the class to use for
authentication logic. The default is `AuthenticationBackend` and will
likely not need to change.

`Authentication.authorization_backend` is the class to use for
authentication logic. The default is `AuthorizationBackend` and will
likely not need to change.

`Authentication.login_html` is the HTML to display for a given user as
the login form.

### `conda_store_server.server.auth.DummyAuthentication`

Has all the configuration settings of `Authetication`. This class is
modeled after the [JupyterHub DummyAuthentication
class](https://github.com/jupyterhub/jupyterhub/blob/9f3663769e96d2e4f665fd6ef485c101704c4645/jupyterhub/auth.py#L1142).

`DummyAuthentication.password` sets a global password for all users to
login with. Effectively a static password. This rarely if ever should
be used outside of testing.

### `conda_store_server.server.auth.GenericOAuthAuthentication`

A provider-agnostic OAuth authentication provider. Configure
endpoints, secrets and other parameters to enable any OAuth-compatible
platform. This class is modeled after the [OAuthenticator OAuth2
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
be requested to OAuth2 provider. This is space separated list of
scopes. Generally only one scope is requested.

`GenericOauthAuthentication.user_data_url` is the API endpoint for
OAuth provider that returns a JSON dict with user data after the user
has successfully authenticated.

`GenericOauthAuthentication.user_data_key` is the key in the payload
returned by `user_data_url` endpoint that provides the `username`.

`GenericOAuthAuthentication.oauth_callback_url` custom callback url
especially useful when web service is behind a proxy.

`GenericOAuthAuthentication.tls_verify` to optionally turn of TLS
verification useful for custom signed certificates.

### `conda_store_server.server.auth.GithubOAuthAuthentication`

Inherits from `Authentication` and `GenericOAuthAuthentication` so
should be fully configurable from those options.

`GithubOAuthAuthentication.github_url` is the url for GitHub. Default
is `https://github.com`.

`GithubOAuthAuthentication.github_api` is the REST API url for
GitHub. Default is `https://api.github.com`.

### `conda_store_server.server.auth.JupyterHubOAuthAuthentication`

Inherits from `Authentication` and `GenericOAuthAuthentication` so
should be fully configurable from those options.

`GithubOAuthAuthentication.jupyterhub_url` is the url for connecting
to JupyterHub. The URL should not include the `/hub/`.

### `conda_store_server.server.app.CondaStoreServer`

`CondaStoreServer.log_level` is the level for all server
logging. Default is `INFO`. Common options are `DEBUG`, `INFO`,
`WARNING`, and `ERROR`.

`CondaStoreServer.enable_ui` a Boolean on whether to expose the UI
endpoints. Default True.

`CondaStoreServer.enable_api` a Boolean on whether to expose the API
endpoints. Default True.

`CondaStoreServer.enable_registry` a Boolean on whether to expose the
registry endpoints. Default True.

`CondaStoreServer.enable_metrics` a Boolean on whether to expose the
metrics endpoints. Default True.

`CondaStoreServer.address` is the address for the server to bind
to. The default is all IP addresses `0.0.0.0`.

`CondaStoreServer.port` is the port for conda-store server to
use. Default is `5000`.

`CondaStoreServer.registry_external_url` is the external hostname and
port to access docker registry cannot contain `http://` or `https://`.

`CondaStoreServer.url_prefix` is the prefix URL (subdirectory) for the
entire application. All but the registry routes obey this. This is due
to the docker registry API specification not supporting url prefixes.

`CondaStoreServer.authentication_class` is the authentication class
for the web server to use. Default is `DummyAuthentication`.

`CondaStoreServer.secret_key` is a secret key needed for some
authentication methods, session storage, etc. TODO: remove at some
point since also used in `AuthenticationBackend`.

`CondaStoreServer.max_page_size` is maximum number of items to return
in a single UI page or API response.

`CondaStoreServer.behind_proxy` indicates if server is behind web
reverse proxy such as Nginx, Traefik, Apache. Will use
`X-Forward-...` headers to determine scheme. Do not set to true if not
behind proxy since Flask will trust any `X-Forward-...` header.

`CondaStoreServer.template` initialized
`fastapi.templating.Jinja2Templates` to use for html templates.

`CondaStoreServer.template_vars` extra variables to be passed into
jinja templates for page rendering.

### `conda_store_server.worker.app.CondaStoreWorker`

`CondaStoreWorker.log_level` is the level for all server
logging. Default is `INFO`. Common options are `DEBUG`, `INFO`,
`WARNING`, and `ERROR`.

`CondaStoreWorker.watch_paths` is a list of paths for conda-store to
watch for changes to directories of `environment.yaml` files or a
single filename to watch.

`CondaStoreWorker.concurrency` by default is not set and defaults to
the number of threads on your given machine. If set will limit the
number of concurrent celery tasks to the integer.

## Frequently Asked Questions

### conda-store fails to build Conda environment and worker is spontaneously killed (9 SIGKILL)

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
