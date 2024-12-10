---
sidebar_position: 1
description: How to install conda-store locally in standalone mode
---

# Standalone (local) installation

The standalone mode is an **experimental feature**, and the quickest way to start using conda-store.
It provisions a complete local setup with conda-store-server running in the background along with [conda-store UI][conda-store-ui] running on localhost.

This installation is recommend for individual users.

## 1. Install the library

:::note
The standalone mode is available in versions 2023.10.1 and later.
:::

Install conda-store-server with  `conda` or `pip`:

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>

<TabItem value="conda" label="conda" default>

```bash
conda install -c conda-forge conda-store-server
```
</TabItem>

<TabItem value="pip" label="pip" default>

```bash
pip install conda-store-server
```
</TabItem>

</Tabs>

## 2. Start in standalone mode

Run the following in the command line:

```bash
conda-store-server  --standalone
```

Access conda-store UI at [`localhost:8080`](https://localhost:8080/) 🎉

## Next steps

Learn to use the [conda-store UI with these tutorials][conda-store-ui-tutorials].


<!-- Internal links -->

[conda-store-ui]: ../../conda-store-ui/introduction
[conda-store-ui-tutorials]: ../../conda-store-ui/tutorials