#!/usr/bin/env bash
set -xe

docker build -f Dockerfile . -t conda-store:dev
docker run \
       -v $PWD/tests/assets/environments:/opt/environments:ro \
       -v /tmp/conda-store/mount:/opt/mount \
       -p 5000:5000 \
       -p 5001:5001 \
       -it conda-store:dev
