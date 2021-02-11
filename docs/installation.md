# Installation

## Kubernetes

The following will describe a local kubernetes installation via
minikube. 

```shell
minikube start --cpus 2 --memory 4096 --driver=docker
```

Now we deploy the `conda-store` components. Note that conda-store is
compatible with any general s3 provider and any general database via
sqlalchemy. Currently the docker image is build with support for
postgresql and sqlite. Consult the [sqlalchemy
documentation](https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls)
on supporting your given database. You may not need to use minio and
postgresql deployments and use existing infrastructure.

```shell
kubectl apply -f minio.yaml
kubectl apply -f postgres.yaml
kubectl apply -f conda-store-worker.yaml
kubectl apply -f conda-store-server.yaml
```
