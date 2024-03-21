<div align="center">
  <img src="./docusaurus-docs/community/images/logos/conda-store-logo-vertical-lockup.svg" alt="conda-store logo" width="30%">
  <p>
  Data science environments, for collaboration.

Flexible. Reproducible. Governable.

  </p>
</div>

---

| Information | Links|
| :---------- | :-----|
| Project | [![License](https://img.shields.io/badge/License-BSD%203--Clause-gray.svg?colorA=2b2d42&colorB=206532&style=flat.svg)](https://opensource.org/licenses/BSD-3-Clause) [![Read the docs](https://img.shields.io/badge/%F0%9F%93%96%20Read-the%20docs-gray.svg?colorA=2b2d42&colorB=206532&style=flat.svg)](https://conda.store)|
|Community | [![Open an issue](https://img.shields.io/badge/%F0%9F%93%9D%20Open-an%20issue-gray.svg?colorA=2b2d42&colorB=206532&style=flat.svg)](https://github.com/conda-incubator/conda-store/issues/new/choose) [![Community guidelines](https://img.shields.io/badge/🤝%20Community-guidelines-gray.svg?colorA=2b2d42&colorB=206532&style=flat.svg)](https://conda.store/community/introduction)|
|Releases | [![PyPI release conda-store](https://img.shields.io/pypi/v/conda-store)](https://badge.fury.io/py/conda-store?label=pypi%20conda-store&style=flat.svg) [![PyPI release conda-store-server](https://img.shields.io/pypi/v/conda-store-server?label=pypi%20conda-store-server)](https://badge.fury.io/py/conda-store-server) [![conda-forge release conda-store](https://img.shields.io/conda/vn/conda-forge/conda-store?label=conda-forge%20conda-store)]((https://anaconda.org/conda-forge/conda-store)) [![conda-forge release conda-store-server](https://img.shields.io/conda/vn/conda-forge/conda-store-server?label=conda-forge%20conda-store-server)]((https://anaconda.org/conda-forge/conda-store-server)) |

---

conda-store provides the familiarity and flexibility of conda environments, without compromising reliability for
collaborative settings.

conda-store is built to work for all team members from individual data scientists to administrators,
while making sure your team follows best practices throughout the environment life cycle:
from initial environment creation to using environments in a production machine.

## Key features

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

## Get started

Learn more, including how to install, use, and contribute to conda-store in our documentation at [**conda.store**](https://conda.store/).

## Contributing

We welcome all types of contributions. Please read our [Contributing Guide](https://conda.store/community/contribute/) to get started.

## Related repositories and projects

- We are working on a new UI for conda-store at [`conda-incubator/conda-store-ui`](https://github.com/conda-incubator/conda-store-ui) and
- a JupyterLab extension at [`conda-incubator/jupyterlab-conda-store`](https://github.com/conda-incubator/jupyterlab-conda-store).

## Code of Conduct

To guarantee a welcoming and friendly community, we require all community members to follow our [Code of Conduct](https://github.com/conda-incubator/governance/blob/main/CODE_OF_CONDUCT.md).

## License

conda-store is developed under the [BSD-3 LICENSED](./LICENSE).
