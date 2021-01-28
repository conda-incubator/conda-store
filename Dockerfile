FROM condaforge/miniforge3:latest

COPY environment.yaml /opt/conda-store/environment.yaml

RUN conda env create -f /opt/conda-store/environment.yaml

COPY conda_store /opt/conda-store/conda_store

ENV PYTHONPATH=/opt/conda-store:${PYTHONPATH}
