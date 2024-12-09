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

- [ ] Prepare the release by running the `cut-release-pr.sh` script

  ```bash
  ./cut-release-pr.sh -r <conda-store version> -c <conda-store-ui version>
  ```

  - [ ] Ensure that the conda-store, conda-store-server, conda-store-ui versions have been updated

  - [ ] Manually review the CHANGELOG and remove/organize important contributions

- [ ] Test that the application is working. In particular, do a manual inspection of the build and `ui` vendoring process:

    ```bash
    cd conda-store-server
    hatch build
    conda-store-server --standalone
    ```

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
