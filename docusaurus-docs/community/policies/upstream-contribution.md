---
description: Upstream contribution policy
---

# Upstream contribution policy

conda-store builds on top of several open source libraries, and critically, many projects in the conda ecosystem.
Contributing back to upstream projects good open source citizenship and the conda-store development team aims to do so wherever relevant.
This policy document outlines some best practices and considerations for upstream contributions.

## Upstream first

As the grounding principle, always prefer contributing features or patches to upstream projects before implementing workarounds or developing conda-store-specific solutions.
This helps us develop better and more sustainable solutions that can benefit a larger community.
If you can unsure about when or how to contribute, open an issue in any conda-store repository and mention the [`@conda-incubator/conda-store`](https://github.com/orgs/conda-incubator/teams/conda-store) team for input.

## Critical upstream projects

conda-store's dependency graph is very large, as is usual for modern open source projects.
Hence, it's not practical to actively contribute back to all of those projects.

To aid in decision-making, the following projects are considered critical for conda-store and contributing to them is encouraged:

* conda
* conda-lock
* conda-pack
* conda-docker

While other project like FastAPI, and pyyaml (see the complete list of dependencies in [`pyproject.toml`][conda-store-server-pyproject] and [on GitHub][conda-store-dependencies]) are not deemed critical, contributions like opening issues and feature requests is encouraged. As direct users of these libraries, conda-store development team in well positioned to share feedback with upstream libraries.

## Contribution guidelines

A non-exhaustive list of good practices to follow when interacting with upstream libraries:

* Always go through and follow the projects' **contribution guidelines** before engaging
* Aspire to open **high-quality** and context-rich issues and pull requests (PRs)
* Before contributing PRs, get **community consensus** on your requested feature or bug-fix, and the implementation strategies
* **Follow-up on your issues** and pull requests diligently to ensure it does not go stale and create additional maintenance tasks for the upstream project
* For critical projects, take the time to improve the documentation, expand the testing suite, help with triage, and other **code-adjacent contributions** that are equally important for the upstream project's overall health
* Share **attributions fairly** while contribution, for example acknowledge code reviewers and advisors through [GitHub's "co-authors" feature for PRs][github-coauthors]

## License considerations

When contributing to an upstream library for the first time, review the project's license. If you need to sign a "Contributor License Agreement" to be able to contribute, share this with conda-store development team to verify the terms.

<!-- Reusable links -->

[conda-store-server-pyproject]: https://github.com/conda-incubator/conda-store/blob/main/conda-store-server/pyproject.toml
[conda-store-dependencies]: https://github.com/conda-incubator/conda-store/network/dependencies
[github-coauthors]: https://docs.github.com/en/pull-requests/committing-changes-to-your-project/creating-and-editing-commits/creating-a-commit-with-multiple-authors
