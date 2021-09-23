FROM condaforge/miniforge3

USER root

ARG GATOR_GIT_URL
ARG GATOR_GIT_BRANCH

COPY environment.yaml /opt/conda-store/environment.yaml

RUN conda env create -f /opt/conda-store/environment.yaml

COPY ./ /opt/conda-store/

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}

RUN cd /opt/conda-store && \
    pip install . && \
    jupyter labextension install jupyterlab-launcher-shortcuts

RUN git clone ${GATOR_GIT_URL} && \
    cd gator && \
    git checkout origin/${GATOR_GIT_BRANCH} && \
    pip install . && \
    yarn install

RUN mkdir -p /opt/jupyterhub && \
    chown -R 1000:1000 /opt/jupyterhub

WORKDIR /opt/jupyterhub
