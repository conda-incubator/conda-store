# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

# conda-store-server Dockerfile
# the generated Docker image is used with docker compose to run the conda-store
# server and public conda-store Docker images

FROM condaforge/miniforge3:24.9.2-0 AS base

LABEL org.opencontainers.image.authors="conda-store development team"

# ensure we are using the conda environment
ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store-server/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}
ENV TZ=Etc/UTC

# must be passed at build environment (should use .python-version-default)
ARG python_version
ARG conda_env_name="conda-store-server"
ARG user_no=1000

RUN apt-get update && \
    # https://docs.anaconda.org/anaconda/install/linux/#installing-on-linux
    apt-get install -yq --no-install-recommends \
    libgl1-mesa-glx \
    libegl1-mesa \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    # needed only for development
    curl && \
    apt-get clean && \
    rm -rf /var/cache/apt/* &&\
    rm -rf /var/lib/apt/lists/* &&\
    rm -rf /tmp/*

# ensure that conda channels is empty by default
# we do not want to tamper with the solve≈
RUN printf 'channels: []\n' > /opt/conda/.condarc && \
    chown -R ${user_no}:${user_no} /opt/conda && \
    mkdir -p /opt/conda-store/conda-store && \
    chown ${user_no}:${user_no} /opt/conda-store/conda-store && \
    mkdir -p /var/lib/conda-store && \
    chown ${user_no}:${user_no} /var/lib/conda-store && \
    mkdir -p /opt/conda-store/envs && \
    chown ${user_no}:${user_no} /opt/conda-store/envs && \
    mkdir /.cache && \
    chown ${user_no}:${user_no} /.cache

USER ${user_no}:${user_no}

RUN mamba create --name ${conda_env_name} \
    python=${python_version} conda \
    --channel conda-forge -y && \
    conda clean --force-pkgs-dirs --all -y

COPY ./ /opt/conda-store-server/

USER 0:0
RUN chown -R ${user_no}:${user_no} /opt/conda-store-server/ && \
    mkdir -p /.local/share/conda-store && \
    chown -R ${user_no}:${user_no} /.local/share/conda-store

USER ${user_no}:${user_no}

# ---------------------------------------------------------------------------------
# for production-ready images we install a specific version of conda-store-server
FROM base AS prod

ARG RELEASE_VERSION

WORKDIR /opt/conda-store-server
RUN which python && \
    python -m pip install conda-store-server==${RELEASE_VERSION} --no-cache-dir && \
    rm -rf /opt/conda-store-server/tests

WORKDIR /var/lib/conda-store
# ---------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# for development images we install conda-store-server in editable mode
FROM base AS dev

WORKDIR /opt/conda-store-server
RUN which python && \
    python -m pip install -e . --no-cache-dir

WORKDIR /var/lib/conda-store
# ---------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# sometimes we need to install the conda-store-server in editable mode with a
# local bundle of the UI
FROM base AS ui-dev

ARG UI_PATH=./conda_store_server/_internal/server/static/conda-store-ui
ENV LOCAL_UI=${UI_PATH}

WORKDIR /opt/conda-store-server

COPY ${UI_PATH}/ /opt/conda-store-server/conda_store_server/UI/dist

RUN which python && \
    python -m pip install -e . --no-cache-dir

WORKDIR /var/lib/conda-store
# ---------------------------------------------------------------------------------
