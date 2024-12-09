---
description: How to install conda-store locally with Docker
---

# Local Docker installation

:::warning
This page is in active development, content may be inaccurate and incomplete.
:::

To install on a local docker daemon there is an existing `docker-compose.yaml` for deployment.
The example files required are in `examples/docker`:

```shell
docker compose up --build
```

On your web browser, visit: [https://conda-store.localhost/conda-store](https://conda-store.localhost/conda-store).

This example uses the JupyterHub OAuth Authenticator. You can log in with the test admin user `admin`, with password `test`.
