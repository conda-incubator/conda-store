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