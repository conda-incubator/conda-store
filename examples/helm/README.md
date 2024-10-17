# Install conda-store with Helm

Setup secrets

```
$ kub create secret generic -n conda-store conda-store-secret --from-file config/config.json 
```

Required values to include:
* `global.condaStoreConfig`
* `global.condaStoreConfigSecretsName`

Helm install 

```
$ helm install conda-store ../../conda-store-server/install/conda-store/  --values values.yaml.env.local
```

Expose the required ports
```
# conda-store UI
$ kubectl port-forward -n conda-store service/conda-store-ui-server 8080:8080  

# minio
$ kubectl port-forward -n conda-store service/minio 30900:9000
```
