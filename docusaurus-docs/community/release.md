---
description: Release process
---

# Release process

This page describes the process for releasing a new version of conda-store.

## Release captain

For every release, there is an assigned "Release Captain". The Release Captain's responsibilities are:

* Manage both the release and testing processes and the documentation as needed.
* Communicate the status of the release to the rest of the conda-store development team and the community.
* Assign owners to checklist items (if not owned by the Release Captain).

## CalVer details

conda-store releases should follow the following CalVer versioning style:

```text
YYYY-MM-releaseNumber
```

:::info
`YYYY` represents the year - such as `2023`

`MM` represents the non-zero padded month - such as `1` for January, `12` for December

`releaseNumber` represents the current release for that month, starting at `1`. Anything above `1` represents a hotfix (patch) release.
:::

:::caution
For the release tag, there should be NO prepended `v`
:::

## Release checklist

Create an issue and copy/paste the steps below to release a new conda-store version. Close the issue when it is done.

:::caution
There are two packages in this repository, [`conda-store`](https://github.com/conda-incubator/conda-store/tree/main/conda-store) and [`conda-store-server`](https://github.com/conda-incubator/conda-store/tree/main/conda-store-server). Make sure to update both packages when releasing a new version.
:::

```md
These steps should be taken in order to create a new release!
**Double check for quality-control**

## Release details

Scheduled release date - <yyyy/mm/dd>

Release captain responsible - <@gh_username>

---

- [ ] There are no [open issues with a `block-release ⛔️` label](https://github.com/conda-incubator/conda-store/issues?q=is%3Aopen+label%3A%22block-release+%E2%9B%94%EF%B8%8F%22+sort%3Aupdated-desc)

**Prepare the codebase for a new version**

- [ ] Create a new git branch for the release `git checkout -b release-2023.9.1`
- [ ] Bump `__version__` in [`conda-store/conda-store/__init__.py`](https://github.com/conda-incubator/conda-store/blob/main/conda-store/conda_store/__init__.py)
- [ ] Bump `__version__` in [`conda-store-server/conda-store-server/__init__.py`](https://github.com/conda-incubator/conda-store/blob/main/conda-store/conda_store/__init__.py)
- [ ] Check the version locally with `hatch version`
- [ ] Make a release commit: ``git commit -m 'RLS: 2023.9.1'``
- [ ] Push the RLS commit ``git push upstream main``
- [ ] If a **release candidate** is needed, tick this box when we're now ready for a full release.

**Make the release**

- [ ] [Start a new GitHub release](https://github.com/conda-incubator/conda-store/releases/new)
    - Call the release the current version, e.g. `2023.9.1`
    - In the **`Choose a Tag:`** dropdown, type in the release name (e.g., `2023.9.1`) and click "Create new tag"
    - In the **`Target:`** dropdown, pin it to the release commit that you've recently pushed.
    - Add release notes in the field below[^github-activity]
- [ ] Confirm that the release completed
    - [The `publish` github action job](https://github.com/pydata/pydata-sphinx-theme/blob/9665190a8a5fbde0de7e7fc6e3608f43de52ec23/.github/workflows/tests.yml#L164-L184) has completed successfully in the [actions tab](https://github.com/pydata/pydata-sphinx-theme/actions).
    - [The PyPI version is updated](https://pypi.org/project/pydata-sphinx-theme/)
- [ ] Celebrate, you're done!


[^github-activity]: If you wish, use [`github-activity` to generate a changelog](https://github.com/choldgraf/github-activity), eg `github-activity conda-incubator/conda-store --since v0.4.15.2 --until v0.3.0`.
```
