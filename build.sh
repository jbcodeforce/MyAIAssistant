#!/bin/bash

set -e

IMAGE_PREFIX="jbcodeforce/myaiassistant"
TAG="${1:-latest}"

echo "Building Docker images with tag: $TAG"

echo "Building backend image..."
docker build -t "${IMAGE_PREFIX}-backend:${TAG}" -f backend/Dockerfile backend/

echo "Building frontend image..."
mkdocs build
docker build -t "${IMAGE_PREFIX}-frontend:${TAG}" -f frontend/Dockerfile .

echo "Build complete."
echo "  - ${IMAGE_PREFIX}-backend:${TAG}"
echo "  - ${IMAGE_PREFIX}-frontend:${TAG}"

