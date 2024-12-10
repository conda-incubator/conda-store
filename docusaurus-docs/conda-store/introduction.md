---
sidebar_position: 1
title: Introduction
description: Introduction to conda-store (core) documentation
---

# conda-store (core)

The [`conda-store` repository on GitHub][conda-store-repo] contains the conda-store application. It has two entrypoints

- **`conda-store-server`**: web server that provides the `conda-store` "service" through a REST API
- **`conda-store-worker`**: celery worker that runs actions for conda-store. For example, building, locking and installing environments

## Get started ✨

The fastest way to get started with conda-store is with a [**local standalone installation**][standalone-install]
and the [**conda-store UI**][conda-store-ui-tutorials].

## Key concepts 🔖

Understand some useful terms and concepts to use conda-store effectively:

* [Essentials for users new to the conda packaging ecosystem][conda-concepts]
* [Concepts and vocabulary unique to conda-store][conda-store-concepts]
* [Descriptions for the artifacts created by conda-store][artifacts]

## Other installation options 💻

conda-store can also be installed using:

* [Docker][install-docker]
* [Kubernetes][install-kubernetes]
* [Vagrant][install-vagrant]

## Deeper dive 📚

Make the most of conda-store by learning about:

* [Performance impact of conda-store components][performance]
* [Configuration options for customization][configuration]
* Internal architecture: [overview][ref-arch], [auth][ref-auth], and [database][ref-database]

## Community and contributing 🌱

Be a part of the conda-store community!
Check out the [Community documentation][community] for details.

<!-- Internal links -->

[standalone-install]: ./how-tos/install-standalone
[conda-store-ui-tutorials]: ../conda-store-ui/tutorials
[explanations]: ./explanations/
[conda-concepts]: ./explanations/conda-concepts
[conda-store-concepts]: ./explanations/conda-store-concepts
[artifacts]: ./explanations/artifacts
[install-docker]: ./how-tos/install-docker
[install-kubernetes]: ./how-tos/install-kubernetes
[install-vagrant]: ./how-tos/install-vagrant
[performance]: ./explanations/performance
[configuration]: ./references/configuration-options
[ref-arch]: ./references/architecture
[ref-auth]: ./references/database
[ref-database]: ./references/auth
[community]: ../community/introduction

<!-- External links -->

[conda-store-repo]: https://github.com/conda-incubator/conda-store
