---
sidebar_position: 6
description: Local development setup for jupyterlab-conda-store
---

# Local setup for JupyterLab extension

## Pre-requisites

- Local [clone of your fork](community/contribute/contribute-code#setup-for-local-development) of the [`jupyterlab-conda-store-ui` repository](https://github.com/conda-incubator/jupyterlab-conda-store)
- [NodeJS `> 18`](https://nodejs.org/en/download/) installed on your local computer to build the extension package.
- Python `>= 3.10` (and `pip`)

## Build and link the extension

:::tip
The `jlpm` command is JupyterLab's pinned version of [yarn](https://yarnpkg.com/) that is installed with JupyterLab.
You may use `yarn` or `npm` in lieu of `jlpm` in the commands below.
:::

1. Navigate to the `jupyterlab-conda-store` directory:

   ```bash
    cd jupyterlab-conda-store
   ```

2. Create and activate a new conda environment:

   ```bash
   conda env create -f environment.yml
   conda activate jupyterlab-conda-store
   ```

3. Install the package in development mode:

   ```bash
   python -m pip install -e .
   ```

4. Now you'll need to link the development version of the extension to JupyterLab and rebuild the Typescript source:

   ```bash
   # Install the extension dependencies
   jlpm install
   # Link your development version of the extension with JupyterLab
   jupyter labextension develop . --overwrite
   ```

5. On the first installation, or after making some changes, to visualize them in your local JupyterLab re-run the following command:

   ```bash
   # Rebuild extension Typescript source after making changes
   jlpm run build
   ```

6. Run JupyterLab and check that the installation worked:

   ```bash
   # Run JupyterLab
   jupyter lab
   ```

:::tip
At times you might need to clean your local repo with the command `npm run clean:slate`. This will clean the repository, and re-install and rebuild.
:::

## Run the tests

You can test your changes locally before opening a pull request.

### Lint and format

To lint files as you work on contributions, you can run:

```bash
jlpm run lint:check
```

### Frontend tests

This extension uses Jest for JavaScript code testing.

To execute them, run:

```
jlpm
jlpm test
```

### Integration tests

This extension uses Playwright for the integration tests (aka user level tests). More precisely, the JupyterLab helper Galata is used to handle testing the extension in JupyterLab.

More information are provided within the [ui-tests README](https://github.com/conda-incubator/jupyterlab-conda-store/blob/main/ui-tests/README.md).

## Uninstall the development version

1. Remove the extension:

   ```bash
   pip uninstall jupyterlab-conda-store
   ```

2. In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
   command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
   folder is located. Then you can remove the symlink named `jupyterlab-conda-store` within that folder.
