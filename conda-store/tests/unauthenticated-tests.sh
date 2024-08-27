#!/usr/bin/env bash
# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

set -euo pipefail

export CONDA_STORE_URL=http://localhost:8080/conda-store
export CONDA_STORE_AUTH=none

conda-store --version
conda-store info
conda-store token
conda-store list namespace
conda-store list build
conda-store list environment
