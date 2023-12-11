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

Create an [issue with the release template](https://github.com/conda-incubator/conda-store/issues/new?assignees=&labels=release+%F0%9F%8F%B7&projects=&template=new-release.md&title=%5BREL%5D+-+%3Crelease+number%3E) to release a new conda-store version. Close the issue when it is done.

:::caution
There are two packages the [conda-store](https://github.com/conda-incubator/conda-store) repository; [`conda-store`](https://github.com/conda-incubator/conda-store/tree/main/conda-store) and [`conda-store-server`](https://github.com/conda-incubator/conda-store/tree/main/conda-store-server). Make sure to update both packages when releasing a new version.
:::

<!-- TODO: Add conda-store-ui and jupyterlab -->
