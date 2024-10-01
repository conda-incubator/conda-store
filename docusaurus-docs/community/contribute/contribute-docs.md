---
sidebar_position: 2
description: Contribute to conda-store's documentation
---

# Contribute documentation

The documentation website is built using [Docusaurus 3][docusaurus] and organized using the [Diátaxis  framework][diataxis] for each conda-store library.

## Style guidelines

conda-store documentation follows the [Nebari documentation style guide][nebari-style-guide] including the [capitalization preferences][nebari-style-guide-capitalization], which in-turn derives from the [Google developer documentation style guide][google-style-guide].

## Documentation structure

All three conda-store libraries are documented in the [`conda-store` GitHub repository][cs-github], in the `docusaurus-docs` folder with each library in a separate sub-folder.

## Contribution process

Similar to code contributions, you can open issues to track as discuss documentation updates and file pull requests to contribute changes.

## Local development setup

### Pre-requisites

1. Fork and clone the conda-store repository: `git clone https://github.com/<your-username>/conda-store.git`
2. Install [Node.js][nodejs], and verify the installed version with `node -v`.

:::tip
To create and activate an isolated conda environment with nodejs, run:

```bash
conda create -n conda-store-docs nodejs
conda activate conda-store-docs
```
:::

### Local development

Navigate to the  `/docusaurus-docs` directory, and run:

```bash
npm install
```

You can then start a development server with the following:

```bash
npm run start
```

This command starts a local development server at [localhost:3000](http://localhost:3000) which opens automatically in a new browser window. Most changes are reflected live without having to restart the server.
The only time you'd need to restart the server is if you are making changes to the documentation site through the `docusaurus.config.js` file.

### Build website

:::note
This is rarely required during development, but can be useful for verifying certain changes. The static files should **not** be committed to the repository.
:::

To build the website locally, run:

```bash
npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

Currently, conda-store docs are deployed using [Netlify][netlify].


<!-- External links -->

[docusaurus]: https://www.nebari.dev/docs/community/style-guide
[diataxis]: https://diataxis.fr
[nebari-style-guide]: https://www.nebari.dev/docs/community/style-guide
[nebari-style-guide-capitalization]: https://www.nebari.dev/docs/community/style-guide#capitalization
[google-style-guide]: https://developers.google.cn/style
[nodejs]: https://nodejs.org/en
[netlify]: https://www.netlify.com
[cs-github]: https://github.com/conda-incubator/conda-store
