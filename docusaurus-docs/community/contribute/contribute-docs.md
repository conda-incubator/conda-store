---
description: Contribute to conda-store's documentation
---

> **Note**
> This page in active development.

The new conda-store documentation website is built using [Docusaurus 2](https://docusaurus.io/) and organized using the [Diátaxis  framework](https://diataxis.fr).

## Local Development

### Pre-requisites

1. Fork and clone the conda-store repository: `git clone https://github.com/<your-username>/conda-store.git`
2. Install [Node.js](https://nodejs.org/en), and verify the installation with `node -v`

### Local development

:::note
You can also create an isolated environment for development.
:::

From the root of the repository, navigate to the `/docusaurus-docs` directory, and run:

```bash
npm install
```

You can then start a development server with the following:

```bash
npm run start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.
The only time you'd need to restart the server is if you are making changes to the documentation site through the `docusaurus.config.js` file.

### Build website

Run:

```bash
npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.
