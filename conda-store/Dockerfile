FROM --platform=linux/amd64 condaforge/mambaforge

USER root

RUN apt-get update \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

COPY environment.yaml /opt/src/conda-store/environment.yaml

RUN mamba env create -f /opt/src/conda-store/environment.yaml

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}

COPY --chown=1000:1000 ./ /opt/src/conda-store/

RUN cd /opt/src/conda-store && \
    pip install -e .

RUN mkdir -p /opt/jupyterhub && \
    chown -R 1000:1000 /opt/jupyterhub

USER 1000:1000

WORKDIR /opt/jupyterhub
