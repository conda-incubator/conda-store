---
title: Introduction
description: Introduction to JupyterLab Extension.
---

# conda-store JupyterLab extension

A extension to use the [conda-store UI][conda-store-ui] - a React-based frontend for conda-store, within JupyterLab.

## Install 📦

1. Pre-requisites: `conda-store-server`, JupyterLab `>=` 3.0 and `<=` 4.0, and Python `>=` 3.8 installed.

2. Install the extension:

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>

<TabItem value="conda" label="conda" default>

```bash
conda install -c conda-forge jupyter-lab-conda-store
```

</TabItem>

<TabItem value="pip" label="pip" default>

```bash
pip install jupyterlab-conda-store
```

</TabItem>

</Tabs>

3. Start JupyterLab:

```bash
jupyter lab
```

4. (Optional) Uninstall the extension

<Tabs>
<TabItem value="conda" label="conda" default>

```bash
conda uninstall jupyter-lab-conda-store
```
</TabItem>
<TabItem value="pip" label="pip" default>

```bash
pip uninstall jupyterlab-conda-store
```
</TabItem>
</Tabs>

## Usage

In the JupyterLab window, click on `conda-store` menu-bar item to open the UI in a new window within JupyterLab.

Learn to use the interface with [conda-store UI tutorials][cs-ui-tutorials].

<!-- Internal links -->

[conda-store-ui]: /conda-store-ui/introduction
[cs-ui-tutorials]: /conda-store-ui/tutorials
