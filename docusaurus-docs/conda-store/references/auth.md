---
description: Authentication and authorization
---

# Auth architecture

:::warning
This page is in active development, content may be incomplete or inaccurate.
:::

## Authentication Model

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
