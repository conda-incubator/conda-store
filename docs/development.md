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

The following resources will be available:
  - conda-store web server running at http://localhost:5000
  - minio s3 running at http://localhost:9000 with username `admin` and password `password`
  - postgres running at localhost:5432 with username `admin` and password `password` database `conda-store`
  - `data` directory in repository containing state:
     - `data/minio` minio state
     - `data/postgres` postgresql state
     - `data/conda-store` conda-store state

