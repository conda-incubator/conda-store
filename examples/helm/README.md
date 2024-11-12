# Install conda-store with Helm

## Setup

### Setup cluster and install dependencies

Start a minkiube cluster

```
$ minikube start
```

Install the dependencies including:
* minio
* postgres
* redis

```
$ kubectl create namespace conda-store
$ kubectl apply -k dependencies
```

View your new service:
```
$ kubectl get po -n conda-store
```

### Setup secrets

```
$ kubectl create secret generic -n conda-store conda-store-secret --from-file config/config.json 
```

Required values to include:
* `global.condaStoreConfig`
* `global.condaStoreConfigSecretsName`

## Helm install 

```
$ helm install conda-store ../../conda-store-server/install/conda-store/  --values values.local.yaml
```

Expose the required ports
```
# conda-store UI
$ kubectl port-forward -n conda-store service/conda-store-ui-server 8080:8080  

# conda-store api
$ kubectl port-forward -n conda-store service/conda-store-ui-server 8080:8081  

# minio
$ kubectl port-forward -n conda-store service/minio 30900:9000
```
