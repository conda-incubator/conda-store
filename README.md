<div align="center">
  <img src="./docusaurus-docs/community/images/logos/conda-store-logo-vertical-lockup.svg" alt="conda-store logo" width="30%">
  <p>
  Data science environments, for collaboration.

  Flexible. Reproducible. Governable.

  </p>
</div>

---

| Information | Links |
|:------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Project     | [![License](https://img.shields.io/badge/License-BSD%203--Clause-gray.svg?&colorB=298642&style=flat.svg)](https://opensource.org/licenses/BSD-3-Clause) [![conda-store documentation](https://img.shields.io/badge/conda--store-documentation%20📖-gray.svg?&colorB=298642&style=flat.svg)](https://conda.store) |
| Releases    | ![GitHub release (the latest by date)](https://img.shields.io/github/v/release/conda-incubator/conda-store?logo=Github) ![PyPI release - conda-store-server](https://img.shields.io/pypi/v/conda-store-server?label=pypi%20conda-store-server) ![PyPI release - conda-store](https://img.shields.io/pypi/v/conda-store-server?label=pypi%20conda-store) ![conda-forge release conda-store-server](https://img.shields.io/conda/vn/conda-forge/conda-store-server?color=298642&label=conda-forge%20conda-store-server) ![conda-forge release conda-store](https://img.shields.io/conda/vn/conda-forge/conda-store?color=298642&label=conda-forge%20conda-store) |

---

<!-- teaser-begin -->

conda-store provides the familiarity and flexibility of conda environments, without compromising reliability for collaborative settings.

conda-store is built to work for all team members from individual data scientists to administrators, while making sure your team follows best practices throughout the environment life cycle: from initial environment creation to using environments in a production machine.

## Key features ✨

- **Flexibility**:
  - Users can create and update environments with the Graphical UI or a YAML editor.
  - The environments are automatically version-controlled and all versions are readily available.
- **Reproducibility**:
  - Users can share environments quickly through the auto-generated artifacts including a lockfile, docker image, YAML file, and tarball.
  - conda-store pins exact versions of all packages and their dependencies in all the auto-generated artifacts.
- **Governance**:
  - Users have access to admin-approved packages and channels for their work and can request new ones when needed.
  - Admins can insert or require certain packages and versions for organization-level compatibility.
  - Admins can manage users' access levels using "Namespaces", and allow users to share environments across (and only with) their team.

## Get started 💻

Learn more, including how to install, use, and contribute to conda-store in our documentation at [**conda.store**](https://conda.store/).

## Related projects 📦

- React-based conda-store UI [`conda-incubator/conda-store-ui`](https://github.com/conda-incubator/conda-store-ui)
- JupyterLab extension [`conda-incubator/jupyterlab-conda-store`](https://github.com/conda-incubator/jupyterlab-conda-store).

## Code of Conduct 🤝

To guarantee a welcoming and friendly community, we require all community members to follow our [Code of Conduct](https://github.com/conda-incubator/governance/blob/main/CODE_OF_CONDUCT.md).

## License 📄

conda-store is developed under the [BSD-3 LICENSE](./LICENSE).
