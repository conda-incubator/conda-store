---
sidebar_position: 1
description: Install conda-store
---

# Install and setup conda-store


## Resource Requirements

`conda-store-server` is a web server and should not require any specific resources.
1 GB of RAM and 1 CPU should be plenty.

`conda-store-worker` does the actual builds of the conda environments.
Solving for conda environments can take a lot of memory in some circumstances.
Make sure to allocate at least 4 GB of RAM to the worker along with at least one CPU.
