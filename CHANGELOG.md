# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

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
 - namespace UI to Conda-Store server #183
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
 - Conda-Store configuration is configured via Traitlets [#87](https://github.com/Quansight/conda-store/pull/87)
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
