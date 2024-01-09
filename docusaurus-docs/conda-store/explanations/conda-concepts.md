---
sidebar_position: 1
description: Understand basics of package management with conda
---

# Conda concepts

conda is a Python package and environment manager, used widely in the Python data science ecosystem.
conda-store build on conda and other supporting libraries in the conda community.
This page briefly covers some key conda concepts necessary to use conda-store.
For detailed explanations, check out the [conda documentation][conda-docs].

## Python package

Open source software projects (sometimes called libraries) are shared with users as *packages*. You need to "install" the package on your local workspace to use it.

[pip][pip-docs] and [conda][conda-docs] are popular package management tools in the Python ecosystem.

pip ships with the Python programming language, and can install packages from the PyPI (Python Package Index) - a community managed collection of packages, public/private PyPI mirrors, GitHub sources, and local directories.

conda needs to be downloaded separately (through a distribution like Anaconda or Miniconda), and can install packages from conda [*channels*](#channels) and local builds.

## Channels (conda)

The [conda documentation][conda-docs-channels] defines:

> Conda channels are the locations where packages are stored. They serve as the base for hosting and managing packages. Conda packages are downloaded from remote channels, which are URLs to directories containing conda packages.

In conda-store, packages are installed from the [conda-forge][conda-forge] channel by default. <!-- NOTE: Verify? -->
conda-forge is a community maintained channel for hosting open source libraries.

:::note
This behavior is different from conda that gets packages from the "default" channel by default.
:::

## Environments

conda-store helps create and manage "conda environments", sometimes also referred to as "data science environments" or simply "environments" in conda-store spaces.

Environments are an isolated set of installed packages.
The [official conda documentation][conda-docs-environments] states:

> A conda environment is a directory that contains a specific collection of conda packages that you have installed.
>
> If you change one environment, your other environments are not affected. You can easily activate or deactivate environments, which is how you switch between them.

## Environment specification (spec)

conda environments are specified through a YAML file, which is called the *environment specification* and has the following major components:

```yaml
name: my-cool-env # name of your environment
channels:   # conda channels to get packages from, in order of priority
   - conda-forge
   - default
dependencies:  # list of packages required for your work
   - python >=3.10
   - numpy
   - pandas
   - matplotlib
   - scikit-learn
   - nodejs # conda can install non-Python packages as well, if it's available on a channel
   - pip
   - pip:   # Optionally, conda can also install packages using pip if needed
      - pytest
```

conda uses this file to create a conda *environment*.

Learn more in the [conda documentation about created an environment file manually][conda-docs-env-file]

## Dependencies

Modern open source software (and software in general) is created using or builds on other libraries, which are called the *dependencies* of the project.
For example, pandas uses NumPy's `ndarray`s and is written partially in Python, hence, NumPy and Python are dependencies of pandas.
Specifically, they are the direct dependencies.
The dependencies of NumPy and pandas, and the dependencies of those dependencies, and so on creates a complete dependency graph for pandas.

Since conda-store focuses on [environments](#environments), the terms *dependencies* usually refers to the full set of compatible dependencies for all the packages specified in an environment.

## Environment creation

Given an `environment.yaml` file, this is how conda perform a build (in brief):

1. Conda downloads `channeldata.json`, a metadata file from each of the channels which
   list the available architectures.

2. Conda then downloads `repodata.json` for each of the architectures
   it is interested in (specifically your particular compute architecture along
   with noarch[^1]). The `repodata.json` has fields like package name,
   version, and dependencies.

[^1]: noarch is a cross-platform architecture which has no OS-specific files. Read [noarch packages in the conda documentation][conda-docs-noarch] for more information.

:::tip
You may notice that the channels listed in the YAML do not have a URL. This
is because in general , non-URL channels are expected to be present at `https://conda.anaconda.org/<channel-name>`.
:::

3. Conda then performs a *solve* to determine the exact version and
   sha256 of each package to download.

4. The specific packages are downloaded.

5. Conda does :sparkles: magic :sparkles: to fix the path prefixes of the installs, which is beyond the scope of this page.

For a detailed walkthrough, check out the [conda install deep dive in the conda documentation][conda-docs-install].

Understand how conda-store builds on conda for improved reproducibility in [conda-store concepts page][conda-store-concepts].

<!-- External links -->
[conda-docs]: https://docs.conda.io/
[pip]: https://pip.pypa.io/en/stable/index.html
[conda-docs-environments]: https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html
[conda-docs-channels]: https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/channels.html#what-is-a-conda-channel
[conda-forge]: https://conda-forge.org/
[conda-docs-env-file]: https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html#creating-an-environment-file-manually
[conda-docs-noarch]: https://docs.conda.io/projects/conda/en/stable/user-guide/concepts/packages.html#noarch-packages
[conda-docs-install]: https://docs.conda.io/projects/conda/en/stable/dev-guide/deep-dives/install.html#fetching-the-index

<!-- Internal links -->
[conda-store-concepts]: conda-store-concepts
