# Conda-store Backwards Compatibility Policy
## Introduction
In software development, it is essential to strike a balance between progress and maintaining a stable environment for existing users. This policy provides guidance on how to the conda-store project will  handle changes to software and services, ensuring that they do not disrupt the workflows of current users, while still enabling innovation and forward progress.
## Breaking versus Non-Breaking Changes

Breaking changes in code refer to modifications or updates made to software that have the potential to disrupt the functionality of existing applications, integrations, or systems.  Breaking changes involve removing existing functionality, altering existing functionality, or adding new requirements. These changes can lead to compatibility issues, causing frustration for end-users, higher maintenance costs, and even system downtime, thus undermining the trust and reputation of the software or service provider.

In contrast, non-breaking changes can add functionality or reduce requirements, allowing software to evolve and grow without negatively impacting existing users. It's important to note that, within this policy, the term "breaking changes" specifically refers to REST API endpoints, database changes, and public Python APIs.

To summarize, users of Conda-Store should be able to upgrade to newer versions without worrying about breaking existing integrations. Newer features will be available for users to adopt when needed, while all existing code should continue to work.

## Specific Implementation Guidance

### Database changes
Databases are one of the most critical areas to ensure there are no breaking changes. Databases hold state for the application. Introducing breaking changes to the Database can be destructive to data and prevent rolling back to earlier versions of conda-store. To maintain backwards compatiblity: 
1. New columns or tables should be added instead of removing or altering existing ones.
2. Columns and tables should not be renamed. Aliases should be used for poorly named existing columns or tables.


### REST API Endpoints

REST API endpoints need to be versioned on a per endpoint basis to allow endpoints to be versioned independently. New endpoints will start at `v1`.

Non-breaking changes do not require a new version of an endpoint. Adding a parameter to the return value of an endpoint or making a previously mandatory input optional can be done without a new endpoint version. However, removing a parameter from the return value, altering the meaning of a value, or making a formerly optional parameter mandatory are breaking changes and would require a new endpoint version. It is not necessary to backport nonbreaking changes to previous versions of endpoints.

#### Experimental changes
Conda-store will expose experimental features within the `experimental` namespace.

For example, if a new version of the `example.com/api/v1/user` endpoint is being tested, but not yet considered stable, it can be made available at the `example.com/api/experimental/user` route. This allows conda-store contributors to test new changes and get community feedback without commiting to supporting a new version of an API endpoint. Using the `experimental` namespace is not mandatory. However, deploying a versioned endpoint does mean a commitment to support that code going forward, so it is highly recommended that developers use the `experimental` namespace to test new endpoints and features before deploying them as stable.

Experimental routes have no guarantees attached to them, they can be removed or changed at any time without warning. This allows testing features with users in real-world scenarios without needing to commit to support that feature as is.

Once endpoints are determined to properly stable and functional, they will be moved into the existing latest version of the API endpoint for non breaking changes or a new version for breaking changes.


#### Example HTTP routes

##### Example: Versioned Stable Route

```
https://example.com/api/v1/user
https://example.com/api/v2/user
```

Explanation: This route has breaking changes between `v1` and `v2`. `v1` will be stable and code written for the `v1` endpoint will continue to function, but all new features will only be available in the `v2` version of the endpoint. This empowers users to upgrade when they wish to rather than forcing them to do so.ss


##### Example: Route That Has Never Had Breaking Changes

```
https://example.com/api/v1/user
```

Explanation: This route has never had breaking changes introduced. Any code written against this endpoint will function regardless of when it was written.

##### Example: new `experimental` route

```
https://example.com/api/experimental/user/
```

Explanation: this is an experimental route. It can be changed or removed at any moment without prior notice. This route should be used to test new features and get community feedback.

#### Removing versions of API endpoints
It is not recommended to remove versions of API endpoints. Removing API endpoints, or versions of endpoints, breaks backwards compatibility and should only be done under exceptional circumstances such as a security vulnerability.

In the case of a removed endpoint, or endpoint version, conda-store should return a status code of `410 Gone` to indicate the endpoint has been removed along with a json object stating when and why the endpoint was removed and what version of the endpoint is available currently (if any).
```
{
	"removalDate": "2021-06-24"
	"removalReason": "Removed to address CVE-2021-32677 (https://nvd.nist.gov/vuln/detail/CVE-2021-32677)"
	"currentEndpointVersion" : "v3"
}
```
### Python API

Public Python modules, classes, functions, methods and variables are considered public APIs and subject to the same considerations as REST API endpoints. Any object that is prepended with an underscore is not considered to be public. This convention is used in the Python community to designate an object as private.

Private examples:
- `_private_func_or_method`
- `_PrivateClass`
- `_PRIVATE_VAR`.

Public examples:
- `public_func_or_method`
- `PublicClass`
- `PUBLIC_VAR`.

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
	# inner is also private - no way to call it without calling _foo, which is private.
```
Tests are never considered to be part of the public API. Any code within the `tests/` directory are always considered to be private.

The only exception to this is code in `tests`. Tests are subject to change or deletion at any time and are never considered to be public code.

Developers are encouraged to make code private by default and only expose objects as public if there is a explicit need to do so. Keeping code private by default limits the public API that the conda-store project developers are commiting to supporting.

#### Types of Objects
##### Modules

A breaking change for a module means that any element of the module's public API has a breaking change.

##### Classes

In a public class, a breaking change is one that changes or removes attributes or methods or alters their meanings. Rather than changing methods or attributes, new methods or attributes should be added if needed. For example, if you wanted to change a user id from an int, to a uuid, a new attribute of User.uuid should be added, and all new code should use User.uuid. Existing methods can use the new attribute or methods as well as long as that doesn't introduce breaking changes for the method.  

##### Functions and Methods
For a function or a method, breaking changes alter the signature of the method or function or the meaning of the return value. t

This means that the parameters (inputs) and return values (outputs) must be the same. Internal logic may be changed as long as it does not change return values. Extra care should be taken when making these changes however. Changing the way a return value is calculated may result in subtle changes which are not obvious. For example, rounding a decimal versus truncating it may return different results even though the function signature remains the same.  

The function signature also includes whether the function is an async function. Changing this is a breaking change.For example, if there is  a function `def list_envs`, which is synchronous, and it should be asynchronous, a new function called `async def list_envs_async` should be added and `list_envs` should be kept as a synchronous call.

Optional parameters may be added as long as they have a specified default value and additional fields may be added to return types if you are returning an object like a dict. These are considered non-breaking.

##### Variables and Constants
Public variables should not have their type changed. 

Public constants should not have their type or their value changed.

#### Deprecating Python APIs

Depreciated Classes, methods, and functions should have a comment in the code stating why they are depreciated and what to use instead. This will encourage developers not to use them without breaking existing code.

```python
"""
This function is deprecated [reason/details], use [replacement] instead
"""
```

Under exceptional circumstances such as a serious security vulnerability which can't be fixed without breaking changes, it may be necessary to depriciate, remove, or introduce breaking changes to objects in the public API. This should be avoided if possible. 


All depreciations shall be communicated in documentation and as part of release notes.
