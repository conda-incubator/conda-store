FROM condaforge/miniforge3

USER root

COPY environment.yaml /opt/conda-store/environment.yaml

RUN conda env create -f /opt/conda-store/environment.yaml

COPY ./ /opt/conda-store/

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}

RUN cd /opt/conda-store && \
    pip install . && \
    pip install https://github.com/Quansight/gator/archive/refs/heads/master.zip && \
    jupyter labextension install jupyterlab-launcher-shortcuts

RUN mkdir -p /opt/jupyterhub && \
    chown -R 1000:1000 /opt/jupyterhub

WORKDIR /opt/jupyterhub
