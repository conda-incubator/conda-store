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

Each of the packages can be released independently.
However, it is recommended to make joint releases to ensure the latest version of `conda-store-ui` is used in `conda-store-server` and in the `jupyterlab-conda-store` extension.
To do so, the releases should be done in the following order:

1. [`conda-store-ui`](https://github.com/conda-incubator/conda-store-ui)
2. [`conda-store-server` and `conda-store`](https://github.com/conda-incubator/conda-store)
3. [`jupyterlab-conda-store`](https://github.com/conda-incubator/jupyterlab-conda-store)

The release process is as follows:

1. **Agree on a release schedule**. We aim to make a monthly conda-store release.
   Though this will depend on whether there are any `release-blocker` issues opened or team availability.The release captain should create an issue with the release date and assign themselves as the release captain.
2. **Start a release**. The release captain should open a `New release` issue on the corresponding repository and assign the issue to themselves.
3. **Prepare and make the release**. The release captain should follow the checklist items in the `New release` issue
   and close the release issues once this is done.
