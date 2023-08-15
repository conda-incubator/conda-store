# Docusaurus documentation

> **Note**
> This website is a work in progress and in active development.

The new conda-store documentation website is built using [Docusaurus 2](https://docusaurus.io/), a modern static website generator.

## Local Development

### Pre-requisites

1. Fork and clone the conda-store repository: `git clone https://github.com/<your-username>/conda-store.git`
2. Install [Node.js](https://nodejs.org/en), and verify installation with: `node -v`

### Local development

Navigate to `docusaurus-docs` repository, and run:

```
npm install
```

You can then start a development server with the following:

```
$ npm run start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Build website

Run:

```
$ npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.
