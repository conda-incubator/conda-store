---
name: "New release 🏷 [maintainers only]"
about: "Start a new conda-store release"
title: "[REL] - <release number>"
labels: ["release 🏷"]
---

<!-- These steps should be taken to create a new release!
**Double-check for quality control** -->

## Release details

Scheduled release date - <yyyy/mm/dd>

Release captain responsible - <@gh_username>

---

### 1. Pre-flight checks

- [ ] Ensure there are no [open issues with a `block-release ⛔️` label](https://github.com/conda-incubator/conda-store/issues?q=is%3Aopen+label%3A%22block-release+%E2%9B%94%EF%B8%8F%22+sort%3Aupdated-desc)

### 2. Prepare the codebase for a new release

- [ ] Create a new git branch for the release `git checkout -b release-2024.9.1`
  - [ ] Prepare the branch just in case `git clean -fxdq`
- [ ] Bump `conda-store` version in [`conda-store/conda-store/__init__.py`](https://github.com/conda-incubator/conda-store/blob/main/conda-store/conda_store/__init__.py)
- [ ] Bump `conda-store-server` version in [`conda-store-server/conda-store-server/__init__.py`](https://github.com/conda-incubator/conda-store/blob/main/conda-store/conda_store/__init__.py)
- [ ] Update the `conda-store-ui` version used in `conda-store-server` [`conda-store-server/hatch_build.py`](https://github.com/conda-incubator/conda-store/blob/main/conda-store-server/hatch_build.py)
- [ ] Update the [CHANGELOG.md](./CHANGELOG.md) file with the new version, release date, and relevant changes[^github-activity].
- [ ] Check the version locally with `hatch version`
- [ ] Build and test locally
  - [ ] For `conda-store` and `conda-store-server`:

    ```bash
    # Note you will need to run this twice, once for each package
    cd conda-store # or cd conda-store-server
    hatch build
    twine check dist/*
    hatch clean
    ```

  - [ ] After building `conda-store-server` and before `hatch clean` run the server in standalone mode:

    ```bash
    cd conda-store-server
    conda-store-server --standalone
    ```

    To do a manual inspection of the build and `ui` vendoring process.

- [ ] Make a release commit: ``git commit -m 'REL - 2024.9.1'``
- [ ] Push the release (REL) commit ``git push upstream main``
- [ ] If a **release candidate** is needed, tick this box when we're ready for a full release.

### 3. Make the release

- [ ] [Start a new GitHub release](https://github.com/conda-incubator/conda-store/releases/new)
  - Call the release the current version, e.g. `2024.9.1`
  - In the **`Choose a Tag:`** dropdown, type in the release name (e.g., `2024.9.1`) and click "Create new tag"
  - In the **`Target:`** dropdown, pin it to the release commit you've recently pushed.
  - Add release notes in the field below[^github-activity]; you can copy/paste the Changelog from the [CHANGELOG.md](./CHANGELOG.md) file.
- [ ] Confirm that the release completed
  - [The `release` GitHub action job](https://github.com/conda-incubator/conda-store/blob/main/.github/workflows/release.yaml) has completed successfully in the [actions tab](https://github.com/pydata/pydata-sphinx-theme/actions).
  - [The `conda-store` PyPI version is updated](https://pypi.org/project/conda-store/)
  - [The `conda-store-server` PyPI version is updated](https://pypi.org/project/conda-store-server/)
  - [The Docker images have been published](https://github.com/conda-incubator/conda-store/blob/main/.github/workflows/build_docker_image.yaml)
- [ ] Update the [conda-forge feedstock version](https://github.com/conda-forge/conda-store-feedstock) through a PR or review and merge the regro-bot PR.
  - [ ] If needed - update `meta.yaml` or `recipe.yaml` and re-render the feedstock.
- [ ] Open a follow-up PR to bump `conda-store` and `conda-store-server` versions to the next dev-release number (for example `2024.10.1`).
- [ ] Open a follow-up PR to bump the `conda-store-server` version in the [`conda-store-ui` compose file](https://github.com/conda-incubator/conda-store-ui/blob/main/docker-compose.yml).
- [ ] Celebrate, you're done! 🎉

[^github-activity]: If you wish, use [`github-activity` to generate a Changelog](https://github.com/choldgraf/github-activity), e.g. `github-activity conda-incubator/conda-store --since 2024.9.1 --until 2023.10.1`.
