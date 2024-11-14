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
* setup secrets

```
$ kubectl create namespace conda-store
$ kubectl apply -k dependencies
```

View your new service:
```
$ kubectl get po -n conda-store
```

View your new secrets:
```
$ kubectl get secret -n conda-store
```

## Generate vaules.local.yaml

Use gomplate to generate the values.local.yaml file. 

If you don't already have gomplate installed, follow [these install instructions](https://docs.gomplate.ca/installing/)

Then, generate the file

```
$ cd tmpl

$ gomplate -d api-server-config.py -d ui-server-config.py -d worker-config.py -d defaults.yaml -f values.local.yaml.tmpl -o ../values.local.yaml
```

## Helm install 

```
$ helm install conda-store ../../conda-store-server/install/conda-store/  --values values.local.yaml
```

Expose the required ports
```
# conda-store UI
$ kubectl port-forward -n conda-store service/conda-store-ui-server 8080:8080  

# conda-store api
$ kubectl port-forward -n conda-store service/conda-store-api-server 8081:8080  

# minio
$ kubectl port-forward -n conda-store service/minio 9000:9000
```

### Check services are up

Check the deployments
```
$ kubectl get deployment -n conda-store
NAME                     READY   UP-TO-DATE   AVAILABLE   AGE
conda-store-api-server   1/1     1            1           15s
conda-store-ui-server    1/1     1            1           15s
conda-store-worker       1/1     1            1           15s
minio                    1/1     1            1           37h
postgres                 1/1     1            1           37h
redis                    1/1     1            1           37h
```

Curl the endpoints
```
# api server
$ curl http://localhost:8081/api/v1/
{"status":"ok","data":{"version":"2024.6.1"},"message":null}%

# ui server
$ curl http://localhost:8080
<!DOCTYPE html>
<html>
    <head>
    . . .
```