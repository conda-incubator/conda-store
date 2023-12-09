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

## Reproducibility of conda

```yaml
name: example
channels:
  - defaults
  - conda-forge
dependencies:
  - python >=3.7
```

Suppose we have the given `environment.yaml` file. How does conda
perform a build?

1. Conda downloads `channeldata.json` from each of the channels which
   list the available architectures.

2. Conda then downloads `repodata.json` for each of the architectures
   it is interested in (specifically your compute architecture along
   with noarch). The `repodata.json` has fields like package name,
   version, and dependencies.

You may notice that the channels listed above do not have a url. This
is because in general you can add
`https://conda.anaconda.org/<channel-name>` to a non-url channel.

3. Conda then performs a solve to determine the exact version and
   sha256 of each package that it will download

4. The specific packages are downloaded

5. Conda does magic to fix the path prefixes of the install

There are two spots that introduce issues to reproducibility. The
first issue is tracking when an `environment.yaml` file has
changes. This can be easily tracked by taking a sha256 of the file
. This is what conda-store does but sorts the dependencies to make
sure it has a way of not triggering a rebuild if the order of two
packages changes in the dependencies list. In step (2) `repodata.json`
is updated regularly. When Conda solves for a user's environment it
tries to use the latest version of each package. Since `repodata.json`
could be updated the next minute the same solve for the same
`environment.yaml` file can result in different solves.

<!-- External links -->
[conda-docs-environments]: https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html
