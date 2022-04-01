FROM --platform=linux/amd64 condaforge/mambaforge

USER root

ARG GATOR_GIT_URL=https://github.com/Quansight/gator.git
ARG GATOR_GIT_BRANCH=change-default-view-for-env

RUN apt-get update \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY environment.yaml /opt/conda-store/environment.yaml

RUN mamba env create -f /opt/conda-store/environment.yaml

COPY ./ /opt/conda-store/

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}

RUN cd /opt/conda-store && \
    pip install . && \
    jupyter labextension install jupyterlab-launcher-shortcuts

RUN git clone ${GATOR_GIT_URL} && \
    cd gator && \
    git checkout origin/${GATOR_GIT_BRANCH} && \
    pip install -e . && \
    jupyter server extension enable mamba_gator --sys-prefix

RUN mkdir -p /opt/jupyterhub && \
    chown -R 1000:1000 /opt/jupyterhub

WORKDIR /opt/jupyterhub
