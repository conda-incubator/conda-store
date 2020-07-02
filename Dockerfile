FROM continuumio/anaconda3:2020.02

COPY conda_store /opt/conda-store/conda_store

ENV PYTHONPATH=/opt/conda-store:${PYTHONPATH}
