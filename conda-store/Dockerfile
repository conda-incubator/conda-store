FROM condaforge/mambaforge:23.3.1-1 as base

LABEL org.opencontainers.image.authors="conda-store development team"

RUN apt-get update &&  \
    apt-get install -yq --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/cache/apt/* &&\
    rm -rf /var/lib/apt/lists/* &&\
    rm -rf /tmp/*   &&\
    groupadd -g 1000 conda-store &&\
    useradd -M -r -s /usr/sbin/nologin -u 1000 -g 1000  conda-store && \
    mkdir -p /opt/jupyterhub && \
    chown -R conda-store:conda-store /opt/jupyterhub

COPY environment.yaml /opt/conda-store/environment.yaml

RUN mamba env create -f /opt/conda-store/environment.yaml && \
    mamba clean --all -y && \
    conda clean --force-pkgs-dirs

# ensure we are using the conda environment
ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}

COPY ./ /opt/conda-store/

# ---------------------------------------------------------------------------------
# for production-ready images we install a specific version of conda-store
FROM base as prod

ARG RELEASE_VERSION

WORKDIR /opt/conda-store
RUN which python && \
    python -m pip install conda-store==${RELEASE_VERSION} --no-cache-dir

USER conda-store
WORKDIR /opt/jupyterhub
# ---------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# for development images we install conda-store-server in editable mode
FROM base as dev

RUN --mount=type=cache,target=/root/.cache/pip cd /opt/conda-store && \
    which python && \
    python -m pip install -e . --no-cache-dir

USER conda-store
WORKDIR /opt/jupyterhub
# ---------------------------------------------------------------------------------
