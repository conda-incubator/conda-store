---
description: How to configure conda-store UI
---

# Configure conda-store UI

The configuration for conda-store-ui, including the connection details to conda-store, can be done :
- either at compile time, using a `.env` file.
- or at runtime, using `condaStoreConfig` variable

### At compile time, using `.env`

conda-store-ui looks for a `.env` file when packing the bundle.
Below, you'll find the options and the listed descriptions. You are welcome to copy this configuration, otherwise, you can copy and rename the `.env.example` file provided in the repository.

Sample File:

```.env
REACT_APP_API_URL=http://localhost:8080/conda-store
REACT_APP_AUTH_METHOD=cookie
REACT_APP_LOGIN_PAGE_URL=http://localhost:8080/conda-store/login?next=
REACT_APP_AUTH_TOKEN=
REACT_APP_STYLE_TYPE=green-accent
REACT_APP_SHOW_AUTH_BUTTON=true
REACT_APP_LOGOUT_PAGE_URL=http://localhost:8080/conda-store/logout?next=/
REACT_APP_URL_BASENAME="/conda-store/ui"
```

### At runtime, using `condaStoreConfig`

When using a webpacked version of `conda-store-ui`, you might want to pass it a configuration.
In your HTML file, add the following **before** loading the react app :

```html
<script>
    const condaStoreConfig = {
        REACT_APP_AUTH_METHOD: "cookie",
        REACT_APP_AUTH_TOKEN: "",
        REACT_APP_STYLE_TYPE: "green-accent",
        REACT_APP_SHOW_AUTH_BUTTON: "true",
        REACT_APP_API_URL: "http://localhost:8080/conda-store",
        REACT_APP_LOGIN_PAGE_URL: "http://localhost:8080/conda-store/login?next=",
        REACT_APP_LOGOUT_PAGE_URL: "http://localhost:8080/conda-store/logout?next=/",
        REACT_APP_URL_BASENAME="/conda-store/ui",
    };
</script>
```

## Docker compose configuration

By default, Docker compose uses the latest release of conda-store-server, but there could be cases where a developer wishes to test against a different versions, such as a release candidate.

Adding the `CONDA_STORE_SERVER_VERSION` variable to the `.env` file will allow overriding this default and setting whichever version of conda-store-server is desired.

## Also see

* [References for configuration options](../references/config-options.md)
