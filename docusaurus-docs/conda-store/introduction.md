---
sidebar_position: 1
title: Introduction
description: Introduction to conda-store (core) documentation
---

# conda-store (core)

The [`conda-store` repository on GitHub][conda-store-repo] consists of two separate, yet related, packages:

- **`conda-store-server`**: web server and workers that together provide the `conda-store` "service" through a REST API
- **`conda-store`** (client): a client which interacts with the service to offer user-facing command line interface

## Quickstart

1. Install conda-store with `conda` or `pip`:

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>

<TabItem value="conda" label="conda" default>

```bash
conda install -c conda-forge conda-store conda-store-server
```
</TabItem>

<TabItem value="pip" label="pip" default>

```bash
pip install conda-store conda-store-server
```
</TabItem>

</Tabs>

2. Start standalone local instance and use the conda-store UI

```bash
conda-store-server  --standalone
```

You can then access conda-store at `localhost:8080` of the machine running it.

3. Use the CLI

```bash
conda-store --help
```

<!-- External links -->

[conda-store-repo]: https://github.com/conda-incubator/conda-store
