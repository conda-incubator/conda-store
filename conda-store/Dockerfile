FROM condaforge/miniforge3:latest

COPY environment.yaml /opt/conda-store/environment.yaml

RUN conda env create -f /opt/conda-store/environment.yaml

COPY ./ /opt/conda-store/

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}

RUN cd /opt/conda-store && \
    yarn && \
    pip install . && \
    jupyter labextension develop . --overwrite && \
    jlpm build
