# Conda Store Extension

This extension for jupyterlab providees kernel management from within the
Jupyter intereface and ecosystem.

## Developing

### Building
*NOTE*: In nixOS, use `conda-shell` and this method will work.

`conda env update -f environment.yaml`

`conda activate conda-store`

`pip install .`

`jupyter labextension develop . --overwrite`

`jlpm run build`

`jupyter lab`


## Documentation

