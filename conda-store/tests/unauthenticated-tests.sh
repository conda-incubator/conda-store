#!/usr/bin/env bash
set -euo pipefail

export CONDA_STORE_URL=http://localhost:8080/conda-store
export CONDA_STORE_AUTH=none

conda-store --version
conda-store info
conda-store token
conda-store list namespace
conda-store list build
conda-store list environment
