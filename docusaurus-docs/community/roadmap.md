# Roadmap

The conda-store roadmap for the remaining part of 2024 into 2025 will revolve around several key areas of iterative improvement:

- Performance
- Backup and restore
- User experience improvements

| Mark | Description      |
| ---- | ---------------- |
| 📪   | work not started |
| ✅   | work completed   |
| ⬆️   | upstream         |
| 🏃   | in progress      |
| 💪   | stretch goal     |


## Performance

[GH Issues](https://github.com/conda-incubator/conda-store/labels/roadmap%3A%20performance)

- ✅ Identify the parts of conda-store responsible for slowing down new environment builds.
    - 🏃 ~40% of environment build time comes from a slow call to conda-lock, which solves each environment twice (once for conda packages and again to support pip packages with a vendored version of poetry). The dependency on conda-lock will be eliminated by implementing official conda support for lockfile generation:
        - ⬆️🏃 Teach conda create how to handle environment.yml files ([#14113](https://github.com/conda/conda/pull/14113))
        - ⬆️🏃 Add support for conda [env] hooks ([#13833](https://github.com/conda/conda/issues/13833)).
        - ⬆️📪 Implement the hooks mentioned above in [conda-pypi](https://github.com/conda-incubator/conda-pypi).
        - ⬆️📪 Define and standardize a conda lockfile schema.
        - ⬆️📪 Replace conda-lock with an officially supported conda plugin for lockfile generation.
    - 🏃 ~40% of environment build time is due to package download and extraction, which is carried out serially to avoid collisions when multiple concurrent requests for the same package are made. Implement a locking mechanism to allow concurrent downloads, reducing this to just the bare network time required to download the required assets.
        - 🏃 Currently, simultaneous calls to conda create result in corrupted packages and cached repo data ([#13037](https://github.com/conda/conda/issues/13037)). Support for locking the repodata cache was added by the community recently ([#12996](https://github.com/conda/conda/pull/12996)), but full locking support must be added to prevent conflicts/data corruption from other concurrent conda operations.
            - ⬆️📪 Add native conda support for locking to allow parallel conda commands on a single machine ([#13055](https://github.com/conda/conda/issues/13055)).

## Storage / Backup and Restore

[GH Issues](https://github.com/conda-incubator/conda-store/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22roadmap%3A%20storage%20%2B%20backup%20%2B%20restore%22)

- 📪 A major concern for existing conda-store deployments is that old, unused builds still take up space on shared volumes. Old builds eventually fill up disk space for deployments with many users, requiring manual intervention to delete them. Implementing a backup mechanism will require reaching consensus on an approach to archiving and recreation old builds ([#889](https://github.com/conda-incubator/conda-store/issues/889)).
    - 📪 Implement archiving of old builds: the yaml spec and the lockfile are kept, but the environments on disk are deleted.
    - 📪 Implement bulk archiving of old builds.
    - 📪 Implement recreation of old builds. Combined with planned performance improvements, users can expect to wait only as long as it takes to download and reinstall the packages for the recreated environment.
- 📪 Transferring or copying a full conda-store deployment is currently not possible. Implement full backup and restore, including creating the active environments on disk.
- 📪 Currently, conda environments created by conda-store do not share packages. In deployments containing many builds, this can lead to many duplicate packages, which uses much more storage than necessary. Refactor the logic around creating new environments so that packages are shared across environments.
- 📪 Design a serialization format upstream for conda environments that captures both the environment specification and the resulting lockfile, paving the path for allowing environments to be transferred reproducibly.
    - 📪 In conda-store, implement the ability to transfer environments along with their histories using the new serialization format.

## User experience improvements

[GH Issues](https://github.com/conda-incubator/conda-store/issues?q=state%3Aopen%20label%3A%22roadmap%3A%20UX%20Experience%22)

- 🏃 Currently there are three ways to interact with the conda-store-server: the CLI, the REST API, and the Python API. However, these interfaces do not provide the same functionality, leading to maintenance issues. Addressing this will require refactoring the existing CLI.
    - ✅ Determine user workflows to scope CLI functionality
    - 📪 Design the new CLI
    - 📪 Implement the new CLI
- 📪 The current conda-store-ui has proven difficult to extend, improve, and maintain. A refactor to simplify and standardize its codebase, while following industry best-practices is currently being proposed which includes updates to the UI to match the new workflows mentioned above.
- 📪 Ensure feature parity between the CLI, REST API, and the Python API
- 🏃 Additional documentation for developers is critical for helping potential contributors, but our current developer documentation does not cover all parts of the code.
    - 🏃 Existing architectural diagrams give an overview of what microservices comprise a complete conda-store deployment. Additional documentation would be useful, particularly to help newcomers understand what conda-store is doing when the user takes various actions.
    - 📪 Additional documentation about authorization and authentication
- 📪 Refactor jupyterlab-conda-store to make it a simple iframe of the existing UI, with cross-iframe messages + URL query parameters for communication and customization.
- 📪 Instead of requiring the user to set an environment variable to build GPU-enabled environments, explicitly add this option to conda-store to make this process smoother.
- 📪 Deprecation of conda-store admin app
- 📪 Implement UX improvements based on recently-completed usability study, and practical issues encountered from dogfooding.

## Operations

[GH Issues](https://github.com/conda-incubator/conda-store/labels/roadmap%3A%20performance)

- 🏃 Provide users (responsible for deploying conda-store) a helm chart with a reasonable reference architecture for deploying conda-store
- 📪 Add Open Telemetry tracing for logging server information for users who are deploying conda-store