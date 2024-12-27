# Conda Store Helm Chart

## TODO:
* use conda-store-ui docker image as the default image for the ui service
* ensure k8 objects are all annotated properly

In order to install conda store with helm, you must
have the following things set up:

## Services
* S3/minio
* DB (eg. Postgres, MySql, etc)
* Redis

## Secrets
* following secrets:
    * conda-store-postgres-secret
    * conda-store-minio-secret
    * conda-store-redis-secret

For example
```
---
apiVersion: v1
data:
  username: YWRtaW4=
  pasword: cGFzc3dvcmQ=
kind: Secret
metadata:
  name: conda-store-postgres-secret
type: Opaque

---
apiVersion: v1
data:
  username: YWRtaW4=
  pasword: cGFzc3dvcmQ=
kind: Secret
metadata:
  name: conda-store-minio-secret
type: Opaque

---
apiVersion: v1
data:
  pasword: cGFzc3dvcmQ=
kind: Secret
metadata:
  name: conda-store-redis-secret
type: Opaque
```

## Volumes

Conda store requires a persistent volume for installing conda environments into. Users should provide a PersistentVolume that binds to the conda-store-worker PVC. For example:

```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: conda-store-environments
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteMany
  volumeMode: Filesystem
  storageClassName: local-storage
  local:  # required for local-storage
    path: /tmp/mnt-vol-kub
  claimRef:
    namespace: conda-store
    name: conda-store-worker-claim
  nodeAffinity:  # required for local-storage
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - mynode
```