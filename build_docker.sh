#!/usr/bin/env bash

IMAGE_HUB="harbor.deepwisdomai.com/deepwisdom/"

IMAGE_NAME="contract_info_extraction"
IMAGE_TAG="v1.0.0"

IMAGE_URL=${IMAGE_HUB}${IMAGE_NAME}:${IMAGE_TAG}

docker build -t ${IMAGE_URL} -f Dockerfile .

docker push ${IMAGE_URL}