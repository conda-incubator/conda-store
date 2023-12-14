---
sidebar_position: 2
description: Create new environments in the UI
---

# 2. Create new environments

## Open the "Create Environment" screen

In the left sidebar, click on the "+" icon next to the namespace where you would like to create a new environment.

In the following image, we create a new environment in the "default" namespace:

![conda-store-ui with plus icon highlighted,which open a new environment creation panel](../images/create-new-env.png)

:::note
In an organization's conda-store, you may have access to create (and edit) environments only in selected namespaces.
If you don't have access, the "+" plus button will be disallowed and displayed in grey.
:::

<!-- TODO: Link to nameaspaces concepts page -->

## Graphical interface

### Add environment name and description

In the environment creation panel, add a suitable name and description for your environment.

![New environment creation screen with name "my-new-environment" and description "Example environment for documentation"](../images/name-description.png)

### Add required packages

In the "Specification" section of the Environment Creation panel, click on the "+ Add Package" button under "Requested Packages":

!["add package" button highlighted](../images/add-package-button.png)

In the text field that opens, start typing the package name and select the package from the list. Once selected, press <kbd>Enter</kbd> to add the package.

![pandas package added](../images/package-selection.png)

Next, select the package version and constrain from the dropdown (you can also type in these fields):

![pandas version 2.1.3 selected](../images/package-version-number.png)

![pandas version set equal 2.1.3, other options are less-than-or-equal, greater-than-or-equal, etc.](../images/package-version-contraint.png)

### Add preferred channel

To specify the (conda) channels you'd like to install packages from, click on the "+ Add Channel" button under "Channels" in the Specification section, type the name of your preferred channel, and press <kbd>Enter</kbd>.

If not specified, the "conda-forge" channel will be used by default.

![Channels subsection under Specification is highlighted where conda-forge is added as a preferred channel](../images/add-channel.png)

### YAML editor

Alternatively, you can use the YAML editor to create environments.
This approach is recommended for users familiar with conda's `environment.yml` specification or for users who need to use `pip` to install some packages.

Click on "Switch to YAML editor" toggle in the Specification section:

![](../images/switch-to-yaml.png)

Update the specification to include the packages, versions, and channels you need.

![](../images/yaml-editor.png)

### Add PyPI-hosted packages (with `pip`)

:::note
You can install packages using `pip` only through the [YAML editor](#yaml-editor).

Currently, pip-installed packages will **not** be visible in the graphical specification. However, these packages will be installed in your environment.
:::

To install packages published only on [PyPI][pypi] using [`pip`][pip], include a `pip` section (add `pip` as a dependency as well) in the YAML editor.

![](../images/pip-section.png)

<!-- TODO:

#### Install from git/mirrors

-->

## Trigger environment creation

Once the name, description, required packages, and channels are specified, click on the "Create" button at the bottom of the screen to trigger environment creation:

![](../images/create-button.png)

A message pops up confirming the environment build. In the "Environment Metadata" section, the "Status" displays "Building" while the environment is created:

![](../images/environment-building.png)

The "Status" will change to "Status: Completed in ... min" once the environment is built and ready to use.


<!-- External links -->

[pypi]: https://pypi.org
[pip]: https://pip.pypa.io/en/stable/installation/
