#!/bin/bash

set -e

IMAGE_PREFIX="jbcodeforce/myaiassistant"
TAG="${1:-latest}"
PLATFORMS="${2:-linux/amd64,linux/arm64}"
PUSH="${3:-false}"

echo "Building Docker images with tag: $TAG for platforms: $PLATFORMS"

# Ensure buildx builder exists and is ready
if ! docker buildx inspect multiarch-builder > /dev/null 2>&1; then
    echo "Creating buildx builder for multi-arch builds..."
    docker buildx create --name multiarch-builder --use
fi
docker buildx use multiarch-builder

# Build arguments for buildx
BUILD_ARGS="--platform ${PLATFORMS}"
if [ "$PUSH" = "true" ]; then
    BUILD_ARGS="${BUILD_ARGS} --push"
else
    BUILD_ARGS="${BUILD_ARGS} --load"
    # --load only works with single platform, fallback to current platform for local builds
    if [[ "$PLATFORMS" == *","* ]]; then
        echo "Note: Multi-platform builds require --push. Building for current platform only for local use."
        BUILD_ARGS="--load"
    fi
fi

echo "Building backend image..."
docker buildx build ${BUILD_ARGS} -t "${IMAGE_PREFIX}-backend:${TAG}" -f backend/Dockerfile backend/

echo "Building frontend image..."
mkdocs build
docker buildx build ${BUILD_ARGS} -t "${IMAGE_PREFIX}-frontend:${TAG}" -f frontend/Dockerfile .

echo "Build complete."
echo "  - ${IMAGE_PREFIX}-backend:${TAG}"
echo "  - ${IMAGE_PREFIX}-frontend:${TAG}"

