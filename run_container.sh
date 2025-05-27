#!/bin/bash

# Check if an image name was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <image-name>"
    exit 1
fi

IMAGE_NAME="$1"

# Allow local connections to the X server for GUI applications in Docker
xhost +local:

# Setup for X11 forwarding to enable GUI
XAUTH=/tmp/.docker.xauth
touch $XAUTH
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -

# Run the Docker container with the selected image and configurations for GUI applications
docker run -it --rm \
    --privileged \
    --network=host \
    --env="LIBGL_ALWAYS_SOFTWARE=0" \
    --env="DISPLAY=$DISPLAY" \
    --env="QT_X11_NO_MITSHM=1" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --env="XAUTHORITY=$XAUTH" \
    --volume="$XAUTH:$XAUTH" \
    --volume="/dev:/dev" \
    --volume="./ros_packages/:/home/nav/ros2_ws/src/" \
    --volume="./gps_navigation_graph:/home/nav/gps_navigation_graph" \
    --device=/dev/dri \
    "$IMAGE_NAME"
