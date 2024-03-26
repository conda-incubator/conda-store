---
sidebar_position: 1
title: Introduction
description: Introduction to conda-store (core) documentation
---

# conda-store (core)

The [`conda-store` repository on GitHub][conda-store-repo] consists of two separate, yet related, packages:

- **`conda-store-server`**: web server and workers that together provide the `conda-store` "service" through a REST API
- **`conda-store`** (client): a client that interacts with the service to offer a user-facing command line interface

## Pre-requisites

- Python `3.8` or later
- `conda`, if installing from scratch we recommend you install [`miniforge`](https://github.com/conda-forge/miniforge) or [`miniconda`](https://docs.anaconda.com/free/miniconda/miniconda-install/).
- `constructor`: https://github.com/conda/constructor

:::warning

`conda` is a hard requirement for `conda-store` and since it is not `pip` installable you need to have `conda` installed before using `conda-store`.

:::

## Quick start

1. Create and activate a new `conda` environment:

```bash
conda create -n conda-store-env python=<Python version of choice>
conda activate conda-store-env
```

2. Install `conda-store` with `conda` or `pip`:

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>

<TabItem value="conda" label="conda" default>

```bash
conda install -c conda-forge conda-store conda-store-server constructor
```

</TabItem>

<TabItem value="pip" label="pip" default>

```bash
# note that we still recommend you use conda to create an environment
# conda create -n conda-store-env python=<Python version of choice>
# conda activate conda-store-env
python -m pip install conda-store conda-store-server

# install constructor
conda install -c conda-forge constructor
```

</TabItem>

</Tabs>

3. Start a standalone local instance and use the `conda-store` UI

```bash
conda-store-server  --standalone
```

You can then access `conda-store` at `localhost:8080` of the machine running it.

4. Use the CLI

```bash
conda-store --help
```

<!-- External links -->

[conda-store-repo]: https://github.com/conda-incubator/conda-store
