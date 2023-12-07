# Conda-Store backwards compatibility policy
## Introduction
In software development, it is essential to strike a balance between progress and maintaining a stable environment for existing users. This policy will provide guidance on how to the Conda-Store project will  handle changes to software and services, ensuring that they do not disrupt or invalidate the experiences of current users, while still enabling innovation and forward progress.
## Breaking versus Non-Breaking Changes

Breaking changes in code refer to modifications or updates made to software that have the potential to disrupt the functionality of existing applications, integrations, or systems.  Breaking changes involve removing existing functionality, altering existing functionality, or adding new requirements. These changes can lead to compatibility issues, causing frustration for end-users, higher maintenance costs, and even system downtime, thus undermining the trust and reputation of the software or service provider.

In contrast, non-Breaking changes can add functionality or reduce requirements. Previously working code will continue to work with non-breaking changes. These changes allow software to evolve and grow without impacting existing users negatively.

Note: the term breaking changes within this policy only refers to REST API endpoints, Database changes and public Python APIs. As long as no breaking changes are introduced to REST API endpoints, Database, or public Python APIs, changes will not be considered breaking.

To summarize: Users of Conda-Store should be able to upgrade to newer versions without worrying that this will break existing integrations. Newer features will be available for users to adopt when they need to, but all existing code should continue to work.

## Specific Implementation Guidance

### Database changes
Databases are one of the most critical areas to ensure there are no breaking changes. Databases hold state for the application and breaking changes to the Database can be destructive to data and prevent rolling back to earlier versions of Conda-Store. To avoid breaking older features, discipline needs to be exercised around database migrations.  
In practice this means:
1. not removing or altering columns, or tables. Instead new columns or tables should be added. This will sometimes mean that data needs to be written to multiple columns, but this is necessary to maintain backwards compatibility.
6. not renaming columns or tables. Aliases should be used to rename existing columns or tables if they are poorly named.


### REST API Endpoints

REST API endpoints need to be versioned. This versioning should be done on a per endpoint basis. This will allow individual endpoints to be versioned independently of each other.

Non-breaking changes do not require a new version of an endpoint. Adding a parameter to the return value of an endpoint or making a previously mandatory input optional can be done without a new endpoint version. However, removing a parameter from the return value, altering the meaning of a value, or making a formerly optional parameter mandatory are breaking changes and would require a new endpoint version.

It is not necessary to backport nonbreaking changes to previous versions of endpoints.

#### Experimental changes
Conda-Store will expose experimental features within the `experimental` namespace.

For example, if a new version of the `example.com/api/user` endpoint is being tested, but not yet considered stable, it can be made available at the `example.com/api/user/experimental` route.

This allows Conda-Store contributors to test new changes and get community feedback without commiting to supporting a new version of an API endpoint.

Note: using the `experimental` namespace is not mandatory. New endpoints and features can be deployed to existing endpoint versions for non-breaking changes and to new versions for breaking changes. However, deploying a versioned endpoint does mean a commitment to support that code going forward, so it is highly encouraged that developers use the `experimental` namespace to test new endpoints and features before deploying them as stable.

Experimental routes have no guarantees attached to them, they can be removed or changed at any time without warning. This allows testing features with users in real-world scenarios without needing to commit to support that feature as is.

Once we determine the routes are stable and want to support them, they will be moved into the existing latest version of the API endpoint for non breaking changes or a new version for breaking changes. If the route is an entirely new endpoint, it will start at `v1`


#### Example HTTP routes

##### Example: versioned stable route

```
https://example.com/v1/api/user
https://example.com/api/v2/user
```

Explanation: This route has breaking changes between `v1` and `v2`. `v1` will be stable, but clients must upgrade to `v2` to benefit from new features.


##### Example: Route that has never had breaking changes

```
https://example.com/api/v1/user
```

Explanation: This route has never had breaking changes introduced.

##### Example: new `experimental` route

```
https://example.com/api/experimental/user/
```

Explanation: this is an experimental route. It can be changed or removed at any moment without prior notice. This route should be used to test new features and get community feedback.

#### Removing versions of API endpoints
It is not recommended to remove versions of API endpoints generally. Removing API endpoints, or versions of endpoints, breaks backwards compatibility and should only be done under exceptional circumstances such as in case of a security vulnerability.

In the case of a removed endpoint, or endpoint version, Conda-Store should return a status code of `410 Gone` to indicate the endpoint has been removed along with a json object stating when and why the endpoint was removed and what version of the endpoint is available currently (if any).
```
{
	"removalDate": "2021-06-24"
	"removalReason": "Removed to address CVE-2021-32677 (https://nvd.nist.gov/vuln/detail/CVE-2021-32677)"
	"currentEndpointVersion" : "v3"
}
```
### Python API

Public Python classes, functions, methods, and so on are considered public APIs and subject to the same considerations as REST API endpoints. The only exception is names starting with a single underscore. This convention is used in the Python community to designate a class, function or method as private.

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

This makes it clear which APIs are public and which are private.

Additionally, any classes, methods, or functions within the `_internal` namespace are considered private by default. It is encouraged that developers use this for any internal logic.

The only exception to this is code in `tests`. Tests are subject to change or deletion at any time and are never considered to be public code.

Any Class, function or method not prepended with a single underscore will be considered public. Developers are encouraged to make all classes, methods, and functions private by default and only expose them as public if there is a legitimate use case. Keeping Classes, functions and methods private by default limits the public APIs that the Conda-Store project developers are commiting to supporting, and

For all public classes, functions, and methods, breaking changes would be anything that changes the class, function, or method's signature or the meaning of a return value.

For a function or a method, this means that the parameters (inputs) and return values (outputs) must be the same. Internal logic may be changed as long as it does not change return values. Extra care should be taken when making these changes however. Changing the way a return value is calculated may result in subtle changes which are not obvious. For example, rounding a decimal versus truncating it may return different results even though the function signature remains the same.  

The function signature also includes whether the function is an async function. Changing this is a breaking change.For example, if there is  a function `def list_envs`, which is synchronous, and it should be asynchronous, a new function called `async def list_envs_async` should be added and `list_envs` should be kept as a synchronous call.

Optional parameters may be added as long as they have a specified default value and additional fields may be added to return types if you are returning an object like a dict. These are considered non-breaking.

For a public class, this means that attributes and methods cannot be removed or changed. Rather than changing methods or attributes, new methods or attributes should be added. For example, if you wanted to change a user id from an int, to a uuid, a new attribute of User.uuid should be added, and all new code should use User.uuid. Existing code can use the new attribute as well as long as that doesn't introduce breaking changes into their signatures.  

Clients should be able to upgrade without any additional changes.

#### Deprecating Python APIs

Depreciated Classes, methods, and functions should have a comment in the code stating why they are depreciated and what to use instead. This will encourage developers not to use them without breaking existing code.

```python
"""
This function is deprecated [reason/details], use [replacement] instead
"""
```

This also shall be communicated on the website and as part of release notes.
