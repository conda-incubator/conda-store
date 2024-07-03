FROM condaforge/mambaforge:23.3.1-1 as base

LABEL org.opencontainers.image.authors="conda-store development team"

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store-server/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}
ENV TZ=Etc/UTC

ARG python_version=3.10
ARG conda_env_name="conda-store-server"

RUN apt-get update && \
    # https://docs.anaconda.org/anaconda/install/linux/#installing-on-linux
    apt-get install -yq --no-install-recommends \
    libgl1-mesa-glx \
    libegl1-mesa \
    libxrandr2 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxi6 \
    libxtst6 \
    # needed only for development
    curl && \
    apt-get clean && \
    rm -rf /var/cache/apt/* &&\
    rm -rf /var/lib/apt/lists/* &&\
    rm -rf /tmp/*

# ensure that conda channels is empty by default
# we do not want to tamper with the solve≈
RUN printf 'channels: []\n' > /opt/conda/.condarc && \
    chown -R 1000:1000 /opt/conda && \
    mkdir -p /opt/conda-store/conda-store && \
    chown 1000:1000 /opt/conda-store/conda-store && \
    mkdir -p /var/lib/conda-store && \
    chown 1000:1000 /var/lib/conda-store && \
    mkdir -p /opt/conda-store/envs && \
    chown 1000:1000 /opt/conda-store/envs && \
    mkdir /.cache && \
    chown 1000:1000 /.cache

USER 1000:1000

RUN mamba create --name ${conda_env_name} python=${python_version} --channel conda-forge -y && \
    conda clean --force-pkgs-dirs --all -y

COPY ./ /opt/conda-store-server/

USER 0:0
RUN chown -R 1000:1000 /opt/conda-store-server/
USER 1000:1000

# ---------------------------------------------------------------------------------
# for production-ready images we install a specific version of conda-store-server
FROM base as prod

ARG RELEASE_VERSION

RUN cd /opt/conda-store-server && \
    mamba activate ${conda_env_name} && \
    python -m pip install conda-store-server==${RELEASE_VERSION} && \
    rm -rf /opt/conda-store-server/tests

WORKDIR /var/lib/conda-store
# ---------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------
# for development images we install conda-store-server in editable mode
FROM base as dev

RUN cd /opt/conda-store-server && \
    mamba activate ${conda_env_name} && \
    python -m pip install -e . --no-cache

WORKDIR /var/lib/conda-store
# ---------------------------------------------------------------------------------
