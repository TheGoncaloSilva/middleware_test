#!/bin/bash

# Detect the host architecture and decide the tag
ARCH=$(uname -m)
TAG="latest-amd64" # Default to amd64
CONTAINER_NAME="subscriber"
IPC_SHARED_CONTAINER_NAME="ipc_share_container"

case "$ARCH" in
    x86_64)
        TAG="latest-amd64"
        ;;
    aarch64)
        TAG="latest-arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Pull the latest version of the Docker image based on the detected architecture
echo "Pulling Docker image for $ARCH..."
docker pull <...>/fastdds-docker:$TAG

# Check if the container is already running and stop it
if [ $(docker ps -q -f name=$CONTAINER_NAME) ]; then
    echo "Stopping running container named $CONTAINER_NAME..."
    docker stop $CONTAINER_NAME
fi

# Check if the container exists (even if it's stopped) and remove it
if [ $(docker ps -aq -f name=$CONTAINER_NAME) ]; then
    echo "Removing existing container named $CONTAINER_NAME..."
    docker rm $CONTAINER_NAME
fi

# Check if the container IPC_SHARED_CONTAINER_NAME exists, if not create it
if [ ! $(docker ps -aq -f name=$IPC_SHARED_CONTAINER_NAME) ]; then
    echo "Creating container named $IPC_SHARED_CONTAINER_NAME..."
    docker run -d --ipc shareable --name $IPC_SHARED_CONTAINER_NAME alpine sleep infinity
fi

# Build the Docker image with the architecture-specific tag
echo "Building Docker image '$CONTAINER_NAME' with tag $TAG..."
docker build --build-arg BASE_IMAGE_TAG=$TAG -t $CONTAINER_NAME -f Dockerfile.dev .

# Run the container in detached mode, mounting the src/ directory
echo "Running container '$CONTAINER_NAME' in detached mode with volume..."
#--ipc container:$IPC_SHARED_CONTAINER_NAME
docker run -itd \
    --network host  \
    --ipc container:$IPC_SHARED_CONTAINER_NAME \
    --name $CONTAINER_NAME \
    -v $(pwd)/src:/root/app $CONTAINER_NAME

# Execute the script inside the container and enter the container's shell in sudo mode
docker exec -it $CONTAINER_NAME su
