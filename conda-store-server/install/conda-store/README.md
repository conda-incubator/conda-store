# Conda Store Helm Chart

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

