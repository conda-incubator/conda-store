#!/usr/bin/env bash
set -xe

docker build -f Dockerfile . -t conda-store:dev
docker run \
       -v $PWD/tests/assets/environments:/opt/environments:ro \
       -v $PWD/mount:/opt/mount \
       -it conda-store:dev
