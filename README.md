Conda Store
-----------------------

Declaratively build conda environments by watching a directory of
`environment.yaml` files. Enabling declarative conda
environments. Environment updates are atomic.

```shell
usage: conda-store.py [-h] -e ENVIRONMENTS [-s STORE] -o OUTPUT
                      [--poll-interval POLL_INTERVAL] [--uid UID] [--gid GID]
                      [--permissions PERMISSIONS]

declarative conda environments on filesystem

optional arguments:
  -h, --help            show this help message and exit
  -e ENVIRONMENTS, --environments ENVIRONMENTS
                        input directory for environments
  -s STORE, --store STORE
                        directory for storing environments and logs
  -o OUTPUT, --output OUTPUT
                        output directory for symlinking conda environment builds
  --poll-interval POLL_INTERVAL
                        poll interval to check environment directory for new
                        environments
  --uid UID             uid to assign to built environments
  --gid GID             gid to assign to built environments
  --permissions PERMISSIONS
                        permissions to assign to built environments
```
