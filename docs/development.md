# Development

## Dependencies

The following are needed for development

 - [docker](https://docs.docker.com/engine/install/)
 - [docker-compose](https://docs.docker.com/compose/install/)

## Docker Compose

To deploy `conda-store` run the following command

```shell
docker-compose up --build
```

Note: If you are not running this command from a Linux `amd64` system, make sure to export `DOCKER_DEFAULT_PLATFORM=linux/amd64` before.

The following resources will be available:
  - conda-store web server running at http://localhost:5000
  - minio s3 running at http://localhost:9000 with username `admin` and password `password`
  - postgres running at localhost:5432 with username `admin` and password `password` database `conda-store`
  - `data` directory in repository containing state:
     - `data/minio` minio state
     - `data/postgres` postgresql state
     - `data/conda-store` conda-store state

## Jupyterlab Extension

To enable the jupyterlab extension, ensure that an instance of `conda-store` is running.

To build, activate the conda-store environemnt. 

Ensure that you are in the `extensions/` folder. 

Then: 

```shell
pip install .
jupyter labextension develop . --overwrite
jlpm build
```

These commands should build the extension. Then, 

`jupyter lab`


