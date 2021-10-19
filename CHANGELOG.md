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
