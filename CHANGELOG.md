# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

 - conda-store and conda-store-server images are now deployed to quay.io/Quansight, which has support for podman and rkt. (#455)

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.4.14] - 2023-04-07

### Fixed

 - make conda-store-ui settings configurable (were previously hardcoded and broken) (#451)

## [0.4.13] - 2023-04-06

### Added

 - Added new conda-store-ui (#444)
 - Added new option `CondaStore.conda_indexed_channels` for indexed channels (#445)
 - Allow passing environment variables in specification (#424)

### Changed

 - Switched to hatch for conda-store and conda-store-server (#449, #450)
 - Switch default UI to conda-store-ui and expose behind `/admin/` (#448) 
 - Significant database rework on package storage for performance (#300)

### Removed

 - Remove unused helm chart (#450)
 - Remove nix flakes from repository (#443)

## [0.4.12] - 2022-09-21

### Fixed

 - environment description is optional

### Added

 - Make symlink path configurable for builds on filesystem #388
 - Redirect on login and cookie handling #381
 - Visually split the namespace with bootstrap bit #374
 - Make image name and tag configurable for uploads to registries #380

## [0.4.11] - 2022-08-17

### Fixed

 - including package_data #379


## [0.4.10] - 2022-08-16

### Added

 - `conda-store-server --standalone` now runs conda-store-server without any service dependencies (#378, #376)
 - Initial helm chart skeleton still work to be done to have official helm chart 

### Fixed

 - Bug in LocalStorage implmentation #376
 - Bug in docker builds when pushed to container registries #377
 - CORS endpoint error on login when using POST #375

## [0.4.9] - 2022-08-09

### Added

 - push/pull container images to/from additionall registries (#370)
 - adding description associated with environments #363

## [0.4.8] - 2022-08-04

### Added

 - Adding shebang support for conda-store (#362)

### Fixed

 - Fixed example demo for docker
 - Fixing docker registry implementation in conda-store (#368)

## Security

 - Adding authentication behind docker registry (#369)

## [0.4.7] - 2022-07-28

### Added

 - Adding additional query parameters environment_id, namespace, name in list api methods in build/environment #350
 - Adding ability to sort based on start/schedule/ended for list builds  #352
 - Adding repo.anaconda.com to default channels #354
 - Empty list for conda_allowed_channels now will allow any channel #358

### Fixed

 - Changed docker images to no longer run as root by default #355

## [0.4.6] - 2022-07-08

### Added

 - Added `c.CondaStoreServer.template_vars` for easy customization #347
 - Consistent naming of `conda-store` throughout project #345
 - Adding token endpoint #335
 - Adding token UI create button #348

### Fixed

 - Bug with user being able to modify `c.RBACAuthorizationBackend.authenticated_role_bindings` #346

## [0.4.5] - 2022-06-29

### Added

 - Adding cli command `solve` to call remote conda solve api (#329)
 - New filters for build and environment api calls status, artifact, package (#329)
 - Adding Alembic migration integration (#314)

## [0.4.4] - 2022-06-25

### Added

 - `wait` option in cli for waiting on artifacts and builds (#328)
 - `list build` command (#328)
 - tests for client conda-store (#328)

### Fixed

 - issue with caching option in run command (#328)

### Changed

 - api now exposes the build_artifacts field on `api/v1/build/<build-id>/`

## [0.4.2] - 2022-06-24

### Fixed

 - fixed release process using build toolchain

## [0.4.1] - 2022-06-24

### Added

 - Command line client for conda-store (#327)
 - Adding searchbar for UI (#326)
 - OpenAPI specification in documentation
 - Added namespace query parameter to `/api/v1/environment/?namespace=` (#324)

## [0.4.0] - 2022-05-04

### Changed

 - Transition to FastAPI for web server from Flask (#277) end user API should not have changed
 - `conda_store_server.server.auth.Authentication.authenticate` is now an `async` method receiving a [Starlette request object](https://www.starlette.io/requests/)

### Added
 
 - Adding PyPi validation for included, required, and default packages (#292)
 - Creating a Conda solve API endpoint (#279)
 - Fully tested API for `/api/v1/...` endpoints (#281)

### Fixed

 - Support for valid `pip` options in `environment.yaml` (#295)


## [0.3.15] - 2022-03-25

### Added

 - Debug mode now controlled by CondaStoreServer.log_level
 - Make concurrency setting optional in configuration
 - Sort namespaces in create environment UI button
 - Allow cookies cross domain

### Fixed

 - Correct default namespace for POST /api/v1/specification/

## [0.3.14] - 2022-03-24

### Added

 - Account for None, "" values within namespace POST in `/api/v1/specification` #274

## [0.3.13] - 2022-03-23

### Added

 - API endpoint `/api/v1/permission/` and UI user endpoint showing user permissions #271

## [0.3.12] - 2022-03-21

### Added

 - better error messages when user not authenticated #261
 - conda package builds independent from conda package download #258
 - exact search route for conda-store api in packages #264
 - adding lockfile to conda-store to provide a short term fix around conda/mamba concurrency issue #268

## [0.3.11] - 2022-03-08

### Added

 - `CondaStore.conda_...` options for managing channels and packages in specification #256
 - Ability to modify/validate specifications server side #252
 - Concurrency option for conda-store celery worker #250
 - Flask webserver has a `CondaStore.behind_proxy` option to properly handle X-Forward- headers #249
 - Docker layer chaching to CI for docker image builds #234

### Changed

 - `buildId` parameter in `/api/v1/environment/<namespace>/<name>/` changed to `build_id` #251

## [0.3.10] - 2022-02-24

### Added

 - `build_id` response to `POST /api/v1/specification` route #244
 - Added a validation for namespaces that is more flexible # 233
 - Added ability to use via `nix run github:quansight/conda-store ...` #232
 - API endpoints now return channel name instead of id #231

### Fixed

 - Flask paths now support routes with and without a trailing slash #230

## [0.3.9] - 2022-01-23

### Added
 
 - Adding support for templates for build and environment symlink directories
 - Adding support for internal and external secure settings

### Fixed

 - Error in build url with extra `/` in environment page

## [0.3.8] - 2022-01-13

### Fixed

 - Ensure compatibility with keycloak authentication flow

## [0.3.7] - 2022-01-13

### Added

 - Support for custom `GenericOAuthAuthentication.oauth_callback_url`
 - Support for optional tls_verification on oauth2 flow `GenericOAuthAuthentication.tls_verify`

## [0.3.6] - 2022-01-12

### Added

 - Testing to support mysql database

## [0.3.5] - 2022-01-11

### Fixed

 - setting fixed sizes to Unicode columns

## [0.3.4] - 2022-01-11

### Added

 - api endpoint for exporting yaml environment files #204

### Fixed

 - using Unicode sqlalchemy column instead of String
 - removed typer as a dependency
 - removed hardcoded path for conda executable
 - environment creation endpoint with namespaces
 - removed psycopg2 as a dependency #206
 - validate that config_file exists #223

## [0.3.3] - 2021-10-28

### Fixed

 - missing dependency in `conda-store-server/setup.py` `yarl`

## [0.3.2] - 2021-10-28

### Added

 - added ability to search within the `/api/v1/build/<build-id>/package/` path #193
 - environments and namespaces no longer show up in API and UI when soft deleted #194

### Fixed

 - `docker-compose.yaml` in `examples/docker` now compatible with 2.0 #195
 - flask templates now included in the PyPi packages #196

## [0.3.1] - 2021-10-12

### Added

 - support for credentials supplied for object storage including IAM credentials #176
 - namespace UI to conda-store server #183
 - create/read/delete methods for namespaces `/api/v1/namespace/` #181
 - distinct_on query parameter to list REST API methods #164
 - adding sorting query parameter to list REST API methods #162
 - ability to filter Conda packages by build parameter #156
 - delete environments and all related builds from REST API #154
 - initial support for pagination for all list REST API methods #126
 - support for filtering environments by name #125
 - working Kubernetes deployment example #116
 - significant documentation effort via multiple PRs

### Changed

 - namespace parameter in JSON POST request to `/api/v1/specification/` #178
 - API route for listing packages within build instead of including within build API response #157
 - database relationship between build, environments, and namespaces improved #153

### Fixed

 - adding conda-store gator extension to `example/docker` #165
 - get query count before applying limits to query #159

## [0.3.0] - 2021-08-27

This is the beginning of the changelog. Here I will list the most
notable things done in the past 3-6 months.

### Added

 - complete authentication and RBAC based authorization modeled after JupyterHub authentication model [#97](https://github.com/Quansight/conda-store/pull/97)
 - support for a namespace associated with environments and builds [#96](https://github.com/Quansight/conda-store/pull/96)
 - testing of conda-store UI via [cypress](https://www.cypress.io/) [#111](https://github.com/Quansight/conda-store/pull/111)
 - delete and update buttons immediately update status [#107](https://github.com/Quansight/conda-store/pull/107)
 - support for dummy authentication and OAuth2 (GitHub + JupyterHub) authentication [#103](https://github.com/Quansight/conda-store/pull/103)
 - delete method for conda-store builds [#94](https://github.com/Quansight/conda-store/pull/94)
 - support for url prefix [#109](https://github.com/Quansight/conda-store/pull/109)
 - docker button says click to copy to clipboard [#110](https://github.com/Quansight/conda-store/pull/110)
 - enabling rollbacks of environment builds [#93](https://github.com/Quansight/conda-store/pull/93)
 - adding `conda env export` for pinned YAML file [#92](https://github.com/Quansight/conda-store/pull/92)
 - celery integration for true task based builds [#90](https://github.com/Quansight/conda-store/pull/90)
 - conda-store configuration is configured via Traitlets [#87](https://github.com/Quansight/conda-store/pull/87)
 - Prometheus metrics endpoint [#84](https://github.com/Quansight/conda-store/pull/84)
 - help button in top right hand corner [#83](https://github.com/Quansight/conda-store/pull/83)
 - support for internal and external url for s3 bucket [#81](https://github.com/Quansight/conda-store/pull/81)

### Changed

 - use Micromamba for environment builds by default [#66](https://github.com/Quansight/conda-store/pull/66)
 - download repodata compressed [#76](https://github.com/Quansight/conda-store/pull/76)
 - only show artifacts once it has been built [#113](https://github.com/Quansight/conda-store/pull/113)
 - true parallel builds and retry if Conda channel update fails [#114](https://github.com/Quansight/conda-store/pull/114)

### Fixed
 
 - SQLAlchemy connection leak to database [#105](https://github.com/Quansight/conda-store/pull/105)
