FROM condaforge/miniforge3:latest

# needed only for development
RUN apt-get update \
    && apt-get install -y wait-for-it \
    && rm -rf /var/lib/apt/lists/*

COPY environment.yaml /opt/conda-store-server/environment.yaml

RUN conda env create -f /opt/conda-store-server/environment.yaml

COPY ./ /opt/conda-store-server/

RUN cd /opt/conda-store-server && \
    /opt/conda/envs/conda-store-server/bin/pip install -e .

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store-server/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}
ENV TZ=America/New_York
