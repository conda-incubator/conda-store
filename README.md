<div align="center">
  <img src="./docs/_static/images/conda-store-logo-vertical-lockup.svg" alt="conda-store logo" width="30%">
  <p>
  Data science environments, for collaboration.

  Flexible. Reproducible. Governable.
  </p>
</div>

---
<div align="center">

  <a href="https://conda-store.readthedocs.io/en/latest/">
    <img src="https://readthedocs.org/projects/conda-store/badge/?version=latest" alt="Documentation Status"/>
  </a>

  <a href="https://pypi.org/project/conda-store-server/">
    <img src="https://img.shields.io/pypi/v/conda-store-server?label=pypi|conda-store-server" alt="PyPi"/>
  </a>

  <a href="https://pypi.org/project/conda-store/">
    <img src="https://img.shields.io/pypi/v/conda-store-server?label=pypi|conda-store" alt="PyPi"/>
  </a>

  <a href="https://anaconda.org/conda-forge/conda-store-server">
    <img src="https://img.shields.io/conda/vn/conda-forge/conda-store-server?color=green&label=conda-forge%7Cconda-store-server" alt="Conda"/>
  </a>

  <a href="https://anaconda.org/conda-forge/conda-store">
    <img src="https://img.shields.io/conda/vn/conda-forge/conda-store?color=green&label=conda-forge%7Cconda-store" alt="Conda"/>
  </a>

</div>

---

conda-store provides the familiarity and flexibility of conda environments, without compromising reliability for collaborative settings.

conda-store is built to work for all team members from individual data scientists to administrators, while making sure your team follows best practices throughout the environment life cycle: from initial environment creation, to using environments in a production machine.

## Key features

* **Flexiblity**:
  * Users can create and update environments with the Graphical UI or a YAML editor.
  * The environments are automatically version-controlled and all versions are readily available.
* **Reproduciblity**:
  * User can share environments quickly through the auto-generated artifacts including a lockfile, docker image, YAML file, and tarball.
  * conda-store pins exact versions of all packages and their dependencies in all the auto-generated artifacts.
* **Goverance**:
  * Users have access to admin-approved packages and channels for their work, and can request new ones when needed.
  * Admins can insert or require certain packages and versions for organization-level compatibility.
  * Admins can manage users' access-levels using "Namespaces", and allow users to share environments across (and only with) their team.

## Get started

Learn more, including how to install, use, and contribute to conda-store in our documentation at [**conda.store**](https://conda.store/).

## Related repositories

- We are working on a new UI for conda-store at: [`Quansight/conda-store-ui`](https://github.com/Quansight/conda-store-ui), and
- a JupyterLab extension at: [`Quansight/jupyterlab-conda-store`](https://github.com/Quansight/jupyterlab-conda-store).

## Code of Conduct

To guarantee a welcoming and friendly community, we require all community members to follow our [Code of Conduct](https://github.com/Quansight/.github/blob/master/CODE_OF_CONDUCT.md).

## License

conda-store is developed under the [BSD-3 LICENSED](./LICENSE).
