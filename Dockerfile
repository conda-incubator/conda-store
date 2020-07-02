FROM continuumio/anaconda3:2020.02

COPY conda_store /opt/conda-store/conda_store
ENV PYTHONPATH=/opt/conda-store:${PYTHONPATH}
ENV TZ=America/New_York

CMD python -m 'conda_store' \
        -p '/opt/environments' \
        -o '/opt/mount/environments' \
        -s '/opt/mount/store' \
        --uid '1000' --gid '100' \
        --permissions '775' \
        --enable-ui --ui-port 5000 \
        --enable-registry --registry-port 5001
