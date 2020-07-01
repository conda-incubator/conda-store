FROM continuumio/anaconda3:2020.02

COPY conda_store /opt/conda-store/conda_store
ENV PYTHONPATH=/opt/conda-store:${PYTHONPATH}

CMD python -m 'conda_store' \
        -p '/opt/environments' \
        -o '/opt/mount/environments' \
        -s '/opt/mount/store' \
        --uid '1000' --gid '100' \
        --permissions '775'
