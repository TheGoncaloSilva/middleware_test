#!/bin/bash

docker buildx build --platform linux/amd64 -t new-fastdds-image -f Dockerfile . --load
docker tag new-fastdds-image:latest <...>/fastdds-docker:latest-amd64
