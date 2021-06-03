FROM condaforge/miniforge3:latest


RUN apt-get update \
    # https://docs.anaconda.org/anaconda/install/linux/#installing-on-linux
    && apt-get install -y libgl1-mesa-glx libegl1-mesa libxrandr2 libxrandr2 libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6 \
    # needed only for development
    && apt-get install -y wait-for-it \
    && rm -rf /var/lib/apt/lists/*

COPY environment.yaml /opt/conda-store-server/environment.yaml

RUN conda env create -f /opt/conda-store-server/environment.yaml

COPY ./ /opt/conda-store-server/

RUN cd /opt/conda-store-server && \
    /opt/conda/envs/conda-store-server/bin/pip install -e .

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store-server/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}
ENV TZ=America/New_York
