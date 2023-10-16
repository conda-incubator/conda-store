FROM --platform=linux/amd64 condaforge/mambaforge:23.3.1-1 as base

LABEL org.opencontainers.image.authors="conda-store development team"

ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store-server/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}
ENV TZ=America/New_York

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
    libxtst6 

# Ensure that conda channels are empty by default
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

# Copy environment.yaml and create a conda environment
COPY environment.yaml /opt/conda-store-server/environment.yaml
RUN mamba env create -f /opt/conda-store-server/environment.yaml && conda clean --force-pkgs-dirs

# Copy the application code
COPY ./ /opt/conda-store-server/

# Install the application
RUN  chown -R 1000:1000 /opt/conda-store-server/ && \
    mkdir /opt/conda/pkgs && \
    chmod 0755 /opt/conda/pkgs 

# Prod Image
FROM --platform=linux/amd64 condaforge/mambaforge:23.3.1-1 as prod
LABEL org.opencontainers.image.authors="conda-store development team"
ARG RELEASE_VERSION
RUN --mount=type=cache,target=/var/lib/apt --mount=type=cache,target=/var/cache/apt \
apt install -y --no-install-recommends curl 
# Copy the conda environment from the builder stage
COPY --from=base /opt/conda /opt/conda
RUN /opt/conda/envs/conda-store-server/bin/pip install conda-store-server==${RELEASE_VERSION} && \
    chown -R 1000:1000 /opt/conda

USER 1000:1000

# Dev Image
FROM --platform=linux/amd64 condaforge/mambaforge:23.3.1-1 as dev
RUN --mount=type=cache,target=/var/lib/apt --mount=type=cache,target=/var/cache/apt \
apt install -y --no-install-recommends curl 
LABEL org.opencontainers.image.authors="conda-store development team"
ARG RELEASE_VERSION
# Copy the conda environment from the builder stage
COPY --from=base /opt/conda /opt/conda
RUN cd /opt/conda-store-server && \
    /opt/conda/envs/conda-store-server/bin/pip install -e . && \
    chown -R 1000:1000 /opt/conda

USER 1000:1000
