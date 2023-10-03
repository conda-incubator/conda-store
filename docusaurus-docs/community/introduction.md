---
sidebar_position: 1
title: Introduction
description: Community documentation
---

# Welcome to conda-store!

conda-store is a set of open source tools for managing data science environments in collaborative teams. It provides flexible-yet-reproducible environments and a user-friendly graphical interface, while enforcing best practices throughout the environment's life cycle.

## Projects

conda-store consists of three projects, developed on separate GitHub repositories:

- [conda-store](https://github.com/conda-incubator/conda-store): the core repository that provides all the key features through a REST API and CLI. Further, the conda-store repository has two packages:
  - conda-store-server: the worker and web server responsible for providing the `conda-store` "service"
  - conda-store: the "client" that users interface with the service
- [conda-store-ui](https://github.com/conda-incubator/conda-store): a frontend application for accessing all the conda-store features
- [jupyterlab-conda-store](https://github.com/conda-incubator/jupyterlab-conda-store): an extension to access `conda-store-ui` within JupyterLab

:::tip
The term "conda-store" is heavily overloaded, it can refer to the overall set of projects, the core repository, or the package based on context.
If the meaning is unclear in a conversation, don't hesitate to ask the people involved to clarify.
:::

## Code of Conduct

The conda-store development team pledges to create a welcoming, supportive, and harassment-free space for everyone. All conda-store spaces, including GitHub conversations and video meetings, are covered by the [conda organization code of conduct](https://github.com/conda-incubator/governance/blob/main/CODE_OF_CONDUCT.md).

## Governance

As a [federated project](https://github.com/conda-incubator/governance/tree/main#federated-projects) under the [conda-incubator organization](https://github.com/conda-incubator), conda-store follows the [conda-incubator governance](https://github.com/conda-incubator/governance/tree/main#conda--conda-incubator-governance). The [conda-store development team (documented through GitHub Teams)](https://github.com/orgs/conda-incubator/teams) makes all project decisions using a [consent-based approach](https://www.sociocracyforall.org/consent-decision-making/) on the issue tracker or in team meetings.

## Support

conda-store's issue trackers are the best way to reach the conda-store development team. If you have any usage or contribution questions, open an issue on the corresponding repository following the [issue creation guidelines][issues]:

* [conda-store](https://github.com/conda-incubator/conda-store/issues/new/choose)
* [conda-store-ui](https://github.com/conda-incubator/conda-store-ui/issues/new/choose)
* [jupyterlab-conda-store](https://github.com/conda-incubator/jupyterlab-conda-store/issues/new/choose)

If you are unsure about the repository, open your issues against the `conda-store`` repository and the development team will move it to the relevant space.

## Contribute

There are many ways in which you can contribute to conda-store (they're all important, so we list them in alphabetical order):

* [Code maintenance and development →][contribute-code]
* Community coordination and contributor experience
* Content translation and internationalization
* DevOps
* Fundraising
* Marketing
* Project management
* [Report bugs and submit feature requests →][issues]
* [Review pull requests →][reviewer-guidelines]
* [Triage issues and pull requests →][triage]
* Website design and development
* [Writing technical documentation →][contribute-docs]
* UI/UX

<!-- TODO: Add links to contribution guidelines for code, docs, and maintenance. -->

<!-- ## Design assets -->

## Acknowledgements

conda-store's community documentation is inspired by the [Nebari community documentation](https://www.nebari.dev/docs/community).


<!-- Internal links -->

[contribute-code]: /community/contribute/contribute-code
[contribute-docs]: /community/contribute/contribute-docs
[triage]: /community/maintenance/triage
[issues]: /community/contribute/issues
[reviewer-guidelines]: /community/maintenance/reviewer-guidelines
