---
sidebar_position: 1
description: Guidelines for contributing to various conda-store projects
---

# Code contribution workflow

We welcome all code contributions to conda-store projects.
This document describes the steps for making successful contributions.

## Select (or open) an issue

The issues marked with the "good first issue" label are a great place to start. These bug reports and feature requests have a low entry-barrier, need little historical context, and are self-contained. Select a project and "good first issue" that matches your interest and skill set.

conda-store development happens across three repositories, and the relevant programming language and technologies are listed below:

* `conda-store` and `conda-store-server`: Python, FastAPI, and conda ecosystem
* `conda-store-ui`: Typescript, React, and frontend web development
* `jupyterlab-conda-store`: JupyterLab extension development (Typescript and Javascript)

:::note
If the issue you are interested in is "assigned" to someone, it means they plan to work on it. In this case, select a different issue or comment on the issue asking the assignee if they are OK with you taking over.
:::

If you feel comfortable contributing the fix/feature directly, write a comment on the issue to let the community know that you are working on it. If you need more context or help with the issue (at any point in your contribution), feel free to ask questions on the same issue.

If your contributing involves significant API changes, write a comment on the issue describing your proposal for implementation. This allows us to discuss the details and confirm the changes beforehand, and respect the time and energy you spend contributing.

The project maintainers are always happy to support you! Please be patient while maintainers get back to your questions, but you can drop a reminder after about 4 working days if no one has replied to you. :)

:::warning
If you want to work on a specific bug or feature that does not have issue, start by [opening a new issue][open-issue] and discussing it before working on it.
:::

## Setup for local development

:::tip
Optionally, you can use tools like conda, pipenv, or venv to create an isolated environment for development.
:::

### Fork and clone the repository

1. Create a personal copy of the corresponding conda-store GitHub repository by clicking the fork button in the top-right corner.

2. Clone the forked project to your local computer:

```bash
git clone https://github.com/<your-username>/<conda-store-repo-name>.git
```

1. Navigate to the project directory.

```bash
cd <conda-store-repo-name>
```

4. Add the upstream repository:

```bash
git remote add upstream https://github.com/conda-incubator/<conda-store-repo-name>.git
```

5. Now the command `git remote -v` shows two remote repositories:

* **upstream:** which refers to the conda-store repository on GitHub.
* **origin:** which refers to your personal fork.

### Install library for development

Follow the steps for the corresponding project to create a development installation:

* [Local setup for conda-store (core)][local-install-conda-store]
* [conda-store-ui][local-install-conda-store-ui]
* [jupyterlab-conda-store][local-install-jlab-conda-store]

## Develop your contribution

1. Before you start, make sure to pull the latest changes from upstream.

```bash
git checkout develop
git pull upstream develop
```

2. Create a branch for the bug or feature you want to work on. The branch name will appear in the merge message, so use a sensible, self-explanatory name:

```bash
git branch feature/<feature name>
git switch feature/<feature name>
# this is an alternative to the git checkout -b feature/<feature name> command
```

3. Commit locally as you progress (`git add` and `git commit`), and make sure to use an adequately formatted commit message.

## Test your contribution

The local setup instructions for the projects also include instructions for testing.
Make sure to test your contributions locally for more efficient code reviews.

## Open a pull requests (PRs)

When you feel comfortable with your contribution, you can open a pull request (PR) to submit it for review

You can also submit partial work to get early feedback on your contribution or discuss some implementation details. If you do so, add WIP (work in progress) in the PR title or add the "status: in progress 🏗" label, and mark it as a draft.

Push your changes back to your fork on GitHub:

```bash
git push origin <feature/feature name>
```

Enter your GitHub username and password (repeat contributors or advanced users can remove this step by connecting to GitHub with SSH).

Go to the corresponding conda-store repository on GitHub. You will see a green pull request button. Make sure the title and message are clear, concise, and self-explanatory. Complete the checklist and read the notes in the PR template, then click the button to submit it.

:::note
If the PR relates to any issues, you can add the text xref gh-xxxx where xxxx is the issue number to GitHub comments. Likewise, if the PR solves an issue, replace the xref with closes, fixes or any other flavors GitHub accepts. GitHub will automatically close the corresponding issue(s) when your PR gets merged.
:::

## Code review

Reviewers (the other developers and interested community members) will write inline and general comments on your pull request (PR) to help you improve its implementation, documentation, and style. Every developer working on the project has their code reviewed, and we've come to see it as a friendly conversation from which we all learn and the overall code quality benefits. Therefore, please don't let the review discourage you from contributing: its only aim is to improve the quality of the project, not to criticize (we are, after all, very grateful for the time you're donating!).

To update your PR to incorporate the suggestions, make your changes on your local repository, commit them, run tests, and only if they succeed, push to your fork. The PR will update automatically as soon as those changes are pushed up (to the same branch as before).

## Guidelines for specific workflows

### Changes to the API

The REST API is considered somewhat stable. If any changes are made to
the API make sure the update the OpenAPI/Swagger specification in
`docs/_static/openapi.json`. This may be downloaded from the `/docs`
endpoint when running conda-store. Ensure that the
`c.CondaStoreServer.url_prefix` is set to `/` when generating the
endpoints.

<!-- Internal links -->

[open-issues]: /community/contribute/issues
[local-install-conda-store]: /community/contribute/local-setup-core
[local-install-conda-store-ui]: /community/contribute/local-setup-ui
[local-install-jlab-conda-store]: /community/contribute/local-setup-labextension
