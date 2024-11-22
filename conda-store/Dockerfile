# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

# conda-store (core) Dockerfile
# the generated Docker image is used with docker compose to run the conda-store
# worker and public conda-store Docker images

FROM condaforge/miniforge3:24.9.2-0 AS base

LABEL org.opencontainers.image.authors="conda-store development team"

# must be passed at build environment (should use .python-version-default)
ARG python_version
ARG conda_env_name="conda-store"
ARG user_no=1000

# ensure we are using the conda environment
ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}

RUN apt-get update &&  \
    apt-get install -yq --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/cache/apt/* &&\
    rm -rf /var/lib/apt/lists/* &&\
    rm -rf /tmp/*   &&\
    groupadd -g ${user_no} conda-store &&\
    useradd -M -r -s /usr/sbin/nologin -u ${user_no} -g ${user_no}  conda-store && \
    mkdir -p /opt/jupyterhub && \
    chown -R conda-store:conda-store /opt/jupyterhub

# MUST keep node in sync with conda-store-ui
RUN mamba create --name ${conda_env_name} \
    python=${python_version} nb_conda_kernels nodejs=18 yarn constructor \
    --channel conda-forge -y && \
    mamba clean --all -y && \
    conda clean --force-pkgs-dirs

COPY ./ /opt/conda-store/

# ---------------------------------------------------------------------------------
# for production-ready images we install a specific version of conda-store
FROM base AS prod

ARG RELEASE_VERSION

WORKDIR /opt/conda-store


RUN which python && \
    python -m pip install conda-store==${RELEASE_VERSION} --no-cache-dir

USER conda-store
WORKDIR /opt/jupyterhub
# ---------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# for development images we install conda-store-server in editable mode
FROM base AS dev

RUN --mount=type=cache,target=/root/.cache/pip
WORKDIR /opt/conda-store

RUN which python && \
    python -m pip install -e . --no-cache-dir

USER conda-store
WORKDIR /opt/jupyterhub
# ---------------------------------------------------------------------------------
