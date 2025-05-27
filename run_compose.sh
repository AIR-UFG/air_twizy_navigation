#!/bin/bash

# Allow local connections to the X server for GUI applications in Docker
xhost +local:

# Define the root directory of the repository
ROOT_DIR=$(pwd)

# Load .env variables from the root of the repository
set -a  # automatically export all variables
source "$ROOT_DIR/.env"
set +a

# Update DISPLAY and XAUTHORITY to ensure GUI works, needed for X11 forwarding
XAUTH=/tmp/.docker.xauth
touch $XAUTH
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -

export DISPLAY=$DISPLAY
export XAUTHORITY=$XAUTH

# Create a volume to share files between the host and the container
# export SHARED_FOLDER="$ROOT_DIR/shared_folder"
# mkdir -p "$SHARED_FOLDER"

# Create a volume to develop ROS packages in the host and share them with the container (ONLY FOR DEVELOPMENT)
# export HOST_FOLDER_PATH="$ROOT_DIR/ros_packages" # Adjusted to match the root relative path
# export CONTAINER_FOLDER_PATH="/root/ros2_ws/src/" # Ensure this matches the container's expected path

# Check if any argument is provided
if [ "$#" -gt 0 ]; then
    # Parse arguments in the form of KEY=value
    for arg in "$@"
    do
        key=$(echo $arg | cut -f1 -d=)
        value=$(echo $arg | cut -f2 -d=)
        
        # Validate the key and update the environment variable
        case "$key" in
            GPU|WORLD_NAME|RVIZ|FOV_UP|FOV_DOWN|WIDTH|HEIGHT|ROBOT_POSE|WITH_VI)
                echo "Setting $key to $value"
                export "$key"="$value"
                ;;
            *)
                echo "Warning: Unknown setting '$key'. Ignored."
                ;;
        esac
    done
fi

# Set GPU-specific Docker Compose configurations
if [ "$GPU" = "true" ]; then
  if [ -z $(which nvidia-smi) ]; then
    echo "NVIDIA GPU support is requested but no NVIDIA GPU found. Running without GPU support."
    export GPU=false
    export NVIDIA_RUNTIME="runc"
  else
    echo "Enabling NVIDIA GPU support."
    export GPU=true
    export NVIDIA_RUNTIME="nvidia"
  fi
else
  echo "Running without NVIDIA GPU support."
  export GPU=false
  export NVIDIA_RUNTIME="runc"
fi

# Function to clean up Docker containers when script is interrupted
cleanup() {
    echo "Shutting down Docker Compose and removing containers..."
    docker compose -f "$ROOT_DIR/docker-compose.yml" down --remove-orphans
}
trap cleanup EXIT

# Ensure the Docker Compose file is found and run
if [ -f "$ROOT_DIR/docker-compose.yml" ]; then
    echo "Running Docker Compose..."
    docker compose -f "$ROOT_DIR/docker-compose.yml" up --build
else
    echo "Docker Compose file not found! Exiting..."
    exit 1
fi