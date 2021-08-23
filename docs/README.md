# Building Documentation

Create the development environment

```shell
cd ../conda-store-server/
conda env create -f environment-dev.yaml
```

Build the documentation

```shell
sphinx-build -b html . _build
```
