FROM --platform=linux/amd64 condaforge/mambaforge

RUN apt-get update \
    # https://docs.anaconda.org/anaconda/install/linux/#installing-on-linux
    && apt-get install -y libgl1-mesa-glx libegl1-mesa libxrandr2 libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6 \
    # needed only for development
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

# ensure that conda channels is empty by default
# we do not want to tamper with the solve
RUN printf 'channels: []\n' > /opt/conda/.condarc

COPY environment.yaml /opt/conda-store-server/environment.yaml

RUN mamba env create -f /opt/conda-store-server/environment.yaml

COPY ./ /opt/conda-store-server/

RUN cd /opt/conda-store-server && \
    /opt/conda/envs/conda-store-server/bin/pip install -e .

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store-server/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}
ENV TZ=America/New_York
