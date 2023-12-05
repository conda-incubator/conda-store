---
description: Understand conda basics
---

# Data science environments

:::warning
This page is in active development.
:::

## Packages/libraries

<!-- TODO -->

## Dependencies

<!-- TODO -->

## Environments

conda-store helps you create and manage "conda environments", also referred to as "data science environments" because `conda` is the leading package and environment management library for the Python data science.

The [official conda documentation][conda-docs-environments] states:

> A conda environment is a directory that contains a specific collection of conda packages that you have installed.
>
> If you change one environment, your other environments are not affected. You can easily activate or deactivate environments, which is how you switch between them.

conda-store is a higher-level toolkit that enforces some conda best practices behind-the-scenes to enable reliable and reproducible environment sharing for collaborative settings.

One of the ways conda-store ensures reproducibility is by auto-generating certain artifacts.

## Channels

<!-- TODO -->

<!-- External links -->
[conda-docs-environments]: https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html
