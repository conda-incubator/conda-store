FROM continuumio/anaconda3:2020.02

COPY conda-store.py /opt/conda-store/conda-store.py

CMD python '/opt/conda-store/conda-store.py' \
        -e '/opt/environments' \
        -o '/opt/mount/environments' \
        -s '/opt/mount/store' \
        --uid '1000' --gid '100' \
        --permissions '775'
