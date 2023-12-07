---
description: Release process
---

# Release process

This page describes the process for releasing a new version of conda-store.

## Release captain

For every release, there is an assigned "Release Captain". The Release Captain's responsibilities are:

* Manage both the release and testing processes and the documentation and release checklists as needed.
* Communicate the status of the release to the rest of the conda-store development team and the community.
* Assign owners to checklist items (if not owned by the Release Captain).

## CalVer details

conda-store, conda-store-ui, and jupyterlab-conda-store releases should follow the following [CalVer](https://calver.org/) versioning style:

```text
YYYY-MM-releaseNumber
```

:::info
`YYYY` represents the year - such as `2023`.

`MM` represents the non-zero padded month - such as `1` for January, `12` for December.

`releaseNumber` represents the current release for that month, starting at `1`. Anything above `1` represents a hotfix (patch) release.

For the release tag, there should be **NO** prepended `v`.
:::

## Release process walkthrough

1. **Agree on a release schedule**. We aim to make a monthly conda-store release. Though this will depend on whether there are any `release-blocker` issues opened or team availability. The release captain should create an issue with the release date and assign themselves as the release captain.
2. **Ensure the main branch builds a package correctly**.
   1. For conda-store and conda-store-server:

    ```bash
        # note you will need to run this twice, once for each package
        cd conda-store # or cd conda-store-server
        git clean -fxdq
        hatch build
    ```

3. **Start a release**. Open an issue and copy & paste the release checklist. Then follow the steps indicated in the release checklist.

:::warning
[jupyterlab-conda-store](https://github.com/conda-incubator/jupyterlab-conda-store) has a direct dependency on [conda-store-ui](https://github.com/conda-incubator/conda-store-ui). Make sure to release conda-store-ui before releasing jupyterlab-conda-store.
:::

### Release checklist (conda-store)

Create an issue and copy & paste the steps below to release a new conda-store version. Close the issue when it is done.

:::caution
There are two packages the [conda-store](https://github.com/conda-incubator/conda-store) repository; [`conda-store`](https://github.com/conda-incubator/conda-store/tree/main/conda-store) and [`conda-store-server`](https://github.com/conda-incubator/conda-store/tree/main/conda-store-server). Make sure to update both packages when releasing a new version.
:::

```md
These steps should be taken to create a new release!
**Double-check for quality control**

## Release details

Scheduled release date - <yyyy/mm/dd>

Release captain responsible - <@gh_username>

---

### 1. Pre-flight checks

- [ ] Ensure there are no [open issues with a `block-release ⛔️` label](https://github.com/conda-incubator/conda-store/issues?q=is%3Aopen+label%3A%22block-release+%E2%9B%94%EF%B8%8F%22+sort%3Aupdated-desc)

### 2. Prepare the codebase for a new release

- [ ] Create a new git branch for the release `git checkout -b release-2023.9.1`
  - [ ] Prepare the branch just in case `git clean -fxdq`
- [ ] Bump `conda-store` version in [`conda-store/conda-store/__init__.py`](https://github.com/conda-incubator/conda-store/blob/main/conda-store/conda_store/__init__.py)
- [ ] Bump `conda-store-server` version in [`conda-store-server/conda-store-server/__init__.py`](https://github.com/conda-incubator/conda-store/blob/main/conda-store/conda_store/__init__.py)
- [ ] Update the `conda-store-ui` version users in `conda-store-server` [`conda-store-server/hatch_build.py`](https://github.com/conda-incubator/conda-store/blob/main/conda-store-server/hatch_build.py)
- [ ] Update the [CHANGELOG.md](./CHANGELOG.md) file with the new version, release date, and relevant changes[^github-activity].
- [ ] Check the version locally with `hatch version`
- [ ] Build and test locally
  - [ ] For `conda-store` and `conda-store-server`:

    ```bash
    # note you will need to run this twice, once for each package
    cd conda-store # or cd conda-store-server
    hatch build
    twine check dist/*
    hatch clean
    ```

- [ ] Make a release commit: ``git commit -m 'REL - 2023.9.1'``
- [ ] Push the release (REL) commit ``git push upstream main``
- [ ] If a **release candidate** is needed, tick this box when we're ready for a full release.

### 3. Make the release

- [ ] [Start a new GitHub release](https://github.com/conda-incubator/conda-store/releases/new)
  - Call the release the current version, e.g. `2023.9.1`
  - In the **`Choose a Tag:`** dropdown, type in the release name (e.g., `2023.9.1`) and click "Create new tag"
  - In the **`Target:`** dropdown, pin it to the release commit that you've recently pushed.
  - Add release notes in the field below[^github-activity], you can copy/paste the changelog from the [CHANGELOG.md](./CHANGELOG.md) file.
- [ ] Confirm that the release completed
  - [The `release` GitHub action job](https://github.com/conda-incubator/conda-store/blob/main/.github/workflows/release.yaml) has completed successfully in the [actions tab](https://github.com/pydata/pydata-sphinx-theme/actions).
  - [The `conda-store` PyPI version is updated](https://pypi.org/project/conda-store/)
  - [The `conda-store-server` PyPI version is updated](https://pypi.org/project/conda-store-server/)
  - [The Docker images have been published](https://github.com/conda-incubator/conda-store/blob/main/.github/workflows/build_docker_image.yaml)
- [ ] Update the [conda-forge feedstock version](https://github.com/conda-forge/conda-store-feedstock) through a PR or review and merge the regro-bot PR.
  - [ ] If needed - update `meta.yaml` or `recipe.yaml` and re-render the feedstock.
- [ ] Celebrate, you're done! 🎉

[^github-activity]: If you wish, use [`github-activity` to generate a changelog](https://github.com/choldgraf/github-activity), eg `github-activity conda-incubator/conda-store --since 2023.9.1 --until 2023.10.1`.

~~~

<!-- TODO: Add conda-store-ui and jupyterlab -->
