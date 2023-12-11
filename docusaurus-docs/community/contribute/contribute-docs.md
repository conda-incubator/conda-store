---
description: Contribute to conda-store's documentation
---

# Contribute documentation

> **Note**
> This page in active development.

The new conda-store documentation website is built using [Docusaurus 2](https://docusaurus.io/) and organized using the [Diátaxis  framework](https://diataxis.fr).

## Local Development

### Pre-requisites

1. Fork and clone the conda-store repository: `git clone https://github.com/<your-username>/conda-store.git`
2. Install [Node.js](https://nodejs.org/en), and verify installation with: `node -v`

### Local development

:::note
You can also create an isolated environment for development.
:::

Navigate to `docusaurus-docs` repository, and run:

```bash
npm install
```

You can then start a development server with the following:

```bash
npm run start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Build website

Run:

```bash
npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

## Storybook

```shell
npm run storybook
```
