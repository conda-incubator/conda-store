---
description: How to install conda-store on local Kubernetes via minikube
---

# Local automated systemd installation

:::warning
This page is in active development, content may be inaccurate and incomplete.
:::

Not all environment are containerized and conda-store recognizes
that. The goal of conda-store is to provide conda environments in as
many ways as possible so it SHOULD support non-contianerized
environments. The example files required are in
`examples/ubuntu2004`.

<!-- TODO: The PR mentioned in the following note is merged.
The note should be updated accordingly. -->

:::note
This example is not fully complete in that it does not install
`conda-store` and get it running due to the [conda-forge
package](https://github.com/conda-forge/staged-recipes/pull/13933).
:::

If you would like to test it in a Virtual machine (VM) use the following:

:::note
The example `Vagrantfile` is only compatible with [libvirt](https://libvirt.org/).
:::

```shell
vagrant up
```

If you want to do a local deployment use:

```shell
ansible-playbook -i <inventory> playbook.yaml
```
