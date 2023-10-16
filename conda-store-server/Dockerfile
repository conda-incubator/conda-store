# Stage 1: Build the application
FROM --platform=linux/amd64 condaforge/mambaforge:23.3.1-1 as builder

# Update and install build dependencies
RUN --mount=type=cache,target=/var/lib/apt --mount=type=cache,target=/var/cache/apt apt update && \
    apt install -y --no-install-recommends \
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
RUN --mount=type=cache,target=/root/.cache/pip ls -la /opt/conda-store-server && \
    cd /opt/conda-store-server && \
    /opt/conda/envs/conda-store-server/bin/pip install . && chown -R 1000:1000 /opt/conda-store-server/ && \
    mkdir /opt/conda/pkgs && \
    chmod 0755 /opt/conda/pkgs 

# Stage 2: Create the runtime image
FROM --platform=linux/amd64 condaforge/mambaforge:23.3.1-1 as prod

# Copy the conda environment from the builder stage
COPY --from=builder /opt/conda /opt/conda

RUN --mount=type=cache,target=/var/lib/apt --mount=type=cache,target=/var/cache/apt \
apt install -y --no-install-recommends curl && \
chown -R 1000:1000 /opt/conda

LABEL org.opencontainers.image.authors="conda-store development team"
USER 1000:1000


# Set environment variables
ENV PATH=/opt/conda/condabin:/opt/conda/envs/conda-store-server/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}
ENV TZ=America/New_York

WORKDIR /var/lib/conda-store
