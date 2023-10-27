#!/usr/bin/env bash
set -euo pipefail

export CONDA_STORE_URL=http://localhost:8080/conda-store
export CONDA_STORE_AUTH=basic
export CONDA_STORE_USERNAME=username
export CONDA_STORE_PASSWORD=password

conda-store --version
conda-store info
conda-store token
conda-store list build
echo "waiting for build 1 to finish"
conda-store wait 1
conda-store wait filesystem/python-flask-env
conda-store wait filesystem/python-flask-env:1
conda-store wait filesystem/python-flask-env:1 --artifact=archive
conda-store list namespace
conda-store list build
conda-store list environment
conda-store list environment --package python --package ipykernel --status COMPLETED --artifact CONDA_PACK
conda-store download 1 --artifact yaml
conda-store download 1 --artifact lockfile
conda-store download 1 --artifact archive
time conda-store run 1 -- python -c "print(1 + 3)"
time conda-store run 1 -- python -c "print(1 + 4)"
