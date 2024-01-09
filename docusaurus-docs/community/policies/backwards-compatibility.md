# conda-store Backwards Compatibility Policy

## Introduction

In software development, it is essential to strike a balance between progress
and maintaining a stable environment for existing users. This policy guides how
the conda-store project will handle changes to software and services, ensuring
that they do not disrupt the workflows of current users, while still enabling
innovation and forward progress.

## Breaking versus non-breaking changes

Breaking code changes refer to modifications or updates made to software that
have the potential to disrupt the functionality of existing applications,
integrations, or systems. Breaking changes involve:

- removing existing functionality
- altering existing functionality
- adding new requirements such as making a previously optional parameter required.

These changes can lead to compatibility issues, causing frustration for
end-users, higher maintenance costs, and even system downtime, thus undermining
the trust and reputation of the software or service provider. Changes are only
breaking if they impact users through the REST API, the Python API, or the
Database.

In contrast, non-breaking changes can add functionality or reduce requirements
such as making a previously required parameter optional.
These changes allow software to evolve and grow without negatively impacting
existing users.

:::info[TL;DR]

conda-store users should be able to upgrade to newer versions without worrying
about breaking existing integrations. Newer features will be available for users
to adopt when needed, while all existing code should continue to work.

:::

## Specific implementation guidance

### Database changes

Databases are one of the most critical areas to ensure there are no breaking
changes. Databases hold the state for the application.  Introducing breaking
changes to the database can be destructive to data and prevent rolling back to
earlier versions of conda-store. To maintain backward compatibility we follow
these principles:

- New columns or tables should be added instead of removing or altering existing
  ones. 
- Columns and tables should not be renamed. Aliases should be used for
  poorly named existing columns or tables.

### REST API endpoints

REST API endpoints are versioned on a per-endpoint basis. New endpoints will
start at `v1`.

Non-breaking changes do not require a new version of an endpoint. For REST API
endpoints, examples on non-breaking changes are:

- adding a parameter to the return value of an endpoint - making a previously
mandatory input optional.

These changes can be done without a new endpoint version.

However, changes such as:

- removing a parameter from the return value - altering the meaning of a value -
making a formerly optional parameter mandatory

are breaking changes and **require** a new endpoint version.

When a new version of an endpoint is created, then all new features will be
added to the new version. 

Older versions of API endpoints are still considered supported and will receive
bug fixes and security updates to their features but new features will not be
backported to them.

#### Experimental changes

conda-store will expose experimental features within the `experimental`
namespace.

For example, if a new version of the `example.com/api/v1/user` endpoint is being
tested, but not yet considered stable, it can be made available at the
`example.com/api/experimental/user` route.  This allows conda-store contributors
to test new changes and get community feedback without committing to supporting
a new version of an API endpoint.  Using the `experimental` namespace is not
mandatory. However, deploying a versioned endpoint expresses a commitment to
support that code going forward, so it is highly recommended that developers use
the `experimental` namespace to test new endpoints and features before marking
them as stable.

Experimental routes have no guarantees attached to them, they can be removed or
changed at any time without warning. This allows testing features with users in
real-world scenarios without needing to commit to support that feature as is.

Once endpoints are determined to be stable and functional, they will be moved
into the existing latest version of the API endpoint for non-breaking changes or
a new version for breaking changes.

#### Example HTTP routes

##### Versioned stable route

``` https://example.com/api/v1/user https://example.com/api/v2/user ```

Explanation: This route has breaking changes between `v1` and `v2`.  Code
written for the `v1` endpoint will continue to function, but all new features
will only be available in the `v2` version of the endpoint.  This empowers users
to upgrade when they wish to rather than forcing them to do so.


##### Route that has never had breaking changes

``` https://example.com/api/v1/user ```

Explanation: This route has never had breaking changes introduced. Any code
written against this endpoint will function regardless of when it was written.

##### New `experimental` route

``` https://example.com/api/experimental/user/ ```

Explanation: This is an experimental route. It can be changed or removed at any
moment without prior notice. This route should be used to test new features and
get community feedback.

#### Removing versions of API endpoints

It is not recommended to remove versions of API endpoints. Removing API
endpoints, or versions of endpoints, breaks backwards compatibility and should
only be done under exceptional circumstances such as a security vulnerability.

If the desire is to prevent a developer from relying on an API endpoint, adding
a warning to the API documentation along with a recommended alternative should
be used rather than a deprecation or removal.

In the case of a removed endpoint, or endpoint version, conda-store should
return a status code of `410 Gone` to indicate the endpoint has been removed
along with a json object stating when and why the endpoint was removed and what
version of the endpoint is available currently (if any).

```python
{
  # the pull request that removed the endpoint
  "reference_pull_request": "https://github.com/conda-incubator/conda-store/pull/0000",
  # the date the endpoint was removed
  "removal_date": "2021-06-24",
  # the reason for the removal, ideally with a link to a CVE if one is available
  "removal_reason": "Removed to address CVE-2021-32677 (https://nvd.nist.gov/vuln/detail/CVE-2021-32677)",
  # the endpoint that developers should use as a replacement
  "new_endpoint": "api/v3/this/should/be/used/instead",
}
```

If an API endpoint must be deprecated, a deprecation warning should be added 
for at least one release before the endpoint is removed. This requirement may
be waived in the case of a serious security vulnerability.

It should always be clearly communicated in release notes and documentation
when an API endpoint is deprecated or removed. This should include:
- version number of the release where this was deprecated
- provide suggestions for alternatives (if possible).
- provide justification for the removal (such as a link to the issue
  or CVE that necessitated the removal)

### Python API

Public Python modules, classes, functions, methods, and variables are considered
public APIs and subject to the same considerations as REST API endpoints. Any
object with a leading underscore is not considered to be public. This convention
is used in the Python community to designate an object as private.

Private examples: - `_private_func_or_method` - `_PrivateClass` -
`_PRIVATE_VAR`.

Public examples: - `public_func_or_method` - `PublicClass` - `PUBLIC_VAR`.

The highest-level entity determines the visibility level.

For example:

```py
class _Private:
  # everything is private here even without underscores
  def this_is_also_private(self): pass
```

or

```py
  def _foo():
    def inner():
    # inner is also private - no way to call it without calling _foo, which is
    # private.
```

Tests are never considered to be part of the public API. Any code within the
`tests/` directory is always considered to be private.

Developers are encouraged to make code private by default and only expose
objects as public if there is an explicit need to do so. Keeping code private by
default limits the public API that the conda-store project developers are
committing to supporting.

#### Deprecating Python APIs

Under exceptional circumstances such as a serious security vulnerability which
can't be fixed without breaking changes, it may be necessary to deprecate,
remove, or introduce breaking changes to objects in the public Python API. 
This should be avoided if possible.

If the desire is to prevent a developer from relying on a part of the Python
API, adding a warning to the documentation along with a recommended alternative
and a comment in the code should be used rather than a deprecation or removal.

```python 
  """
  This function is deprecated [reason/details], use [replacement] instead
  """
```
If part of the Python API must be deprecated or removed, a deprecation warning
should be added for at least one release before the endpoint is removed. This
requirement may be waived in the case of a serious security vulnerability.

The deprecation or removal should always be clearly communicated in release
notes and documentation This should include:
- version number of the release where this was deprecated
- provide suggestions for alternatives (if possible).
- provide a reason for the deprecation or removal (such
  as a link to a CVE or issue that necessitated the removal

#### Types of objects

##### Modules

A breaking change for a module means that any element of the module's public API
has a breaking change.

##### Classes

In a public class, a breaking change is one that changes or removes attributes
or methods or alters their meanings.  Rather than changing methods or
attributes, new methods or attributes should be added if needed.  For example,
if you wanted to change a user id from an `int`, to a `uuid`, a new attribute
`User.uuid` should be added, and all new code should use `User.uuid`.  Existing
methods can use the new attribute or methods as well as long as that doesn't
introduce breaking changes for the method.

##### Functions and methods

For a function or a method, breaking changes alter its signature or the meaning
of the return value.

This means that the parameters (inputs) and return values (outputs) must be the
same. Internal logic may be changed as long as it does not change return values.
Extra care should be taken when making these changes however. Changing the way a
return value is calculated may result in subtle changes which are not obvious.
For example, rounding a decimal versus truncating it may return different
results even though the function signature remains the same.

The function signature also includes whether the function is an async function.
Changing this is a breaking change.

For example, if there is a function `list_envs`, which is synchronous, and
it should be asynchronous, a new function called ` list_envs_async` should be
added and `list_envs` should be kept as a synchronous call.

Optional parameters may be added as long as they have a specified default value
and additional fields may be added to return types if you are returning an
object like a dict. These are considered non-breaking.

##### Variables and constants

Public variables should not have their type changed.

Public constants should not have their type or their value changed.
