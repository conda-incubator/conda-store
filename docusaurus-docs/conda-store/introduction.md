---
sidebar_position: 1
title: Introduction
description: Introduction to conda-store (core) documentation
---

# conda-store (core)

The [`conda-store` repository on GitHub][conda-store-repo] consists of two separate, yet related, packages:

- **`conda-store-server`**: web server and workers that together provide the `conda-store` "service" through a REST API
- **`conda-store` (client)**: a client that interacts with the service to offer a user-facing command line interface (CLI)

## Get started ✨

The fastest way to get started with conda-store is with a [**local standalone installation**][standalone-install/introduction]
and the [**conda-store UI**][conda-store-ui-tutorials/introduction].

Alternatively, you can use some features of conda-store through the [CLI commands][cli-ref/introduction] or as a [shebang][shebang/introduction].

## Key concepts 🔖

Understand some useful terms and concepts to use conda-store effectively:

* [Essentials for users new to the conda packaging ecosystem][conda-concepts/introduction]
* [Concepts and vocabulary unique to conda-store][conda-store-concepts/introduction]
* [Descriptions for the artifacts created by conda-store][artifacts/introduction]

## Other installation options 💻

conda-store can also be installed using:

* [Docker][install-docker/introduction]
* [Kubernetes][install-kubernetes/introduction]
* [Vagrant][install-vagrant/introduction]

## Deeper dive 📚

Make the most of conda-store by learning about:

* [Performance impact of conda-store components][performance/introduction]
* [Configuration options for customization][configuration/introduction]
* Internal architecture: [overview][ref-arch/introduction], [auth][ref-auth/introduction], and [database][ref-database/introduction]

## Community and contributing 🌱

Be a part of the conda-store community!
Check out the [Community documentation][community/introduction] for details.

<!-- Internal links -->

[standalone-install/introduction]: ./how-tos/install-standalone
[conda-store-ui-tutorials/introduction]: ../conda-store-ui/tutorials
[cli-ref/introduction]: ./references/cli
[shebang/introduction]: ./how-tos/shebang
[explanations/introduction]: ./explanations/
[conda-concepts/introduction]: ./explanations/conda-concepts
[conda-store-concepts/introduction]: ./explanations/conda-store-concepts
[artifacts/introduction]: ./explanations/artifacts
[install-docker/introduction]: ./how-tos/install-docker
[install-kubernetes/introduction]: ./how-tos/install-kubernetes
[install-vagrant/introduction]: ./how-tos/install-vagrant
[performance/introduction]: ./explanations/performance
[configuration/introduction]: ./references/configuration-options
[ref-arch/introduction]: ./references/architecture
[ref-auth/introduction]: ./references/database
[ref-database/introduction]: ./references/auth
[community/introduction]: ../community/introduction

<!-- External links -->

[conda-store-repo]: https://github.com/conda-incubator/conda-store
