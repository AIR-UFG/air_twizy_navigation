FROM osrf/ros:iron-desktop-full

RUN apt-get update && apt-get install -y \
    wget \
    python3-pip \
    python3-rosdep \
    ros-iron-gazebo-ros \
    ros-iron-gazebo-dev \
    ros-iron-gazebo-plugins \
    ros-iron-gazebo-ros-pkgs \
    ros-iron-joint-state-publisher \
    ros-iron-velodyne* \
    ros-iron-ackermann* \
    ros-iron-can-msgs \
    ros-iron-robot-localization\
    ros-iron-mapviz \
    ros-iron-mapviz-plugins \
    ros-iron-tile-map \
    ros-iron-turtlebot3-gazebo \
    ros-iron-navigation2 \
    ros-iron-nav2-bringup \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/nav

RUN mkdir -p /ros2_ws/src
COPY ./ros_packages /home/nav/ros2_ws/src/

RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash \ 
                  && apt-get update && cd /home/nav/ros2_ws && rosdep install --from-paths src --ignore-src -r -y \
                  && colcon build --packages-ingore nav2_costmap_2d \
                  && MAKEFLAGS='-j2' colcon build --packages-select nav2_costmap_2d"

RUN mkdir -p /root/.gazebo/models \
&& cp -r ros2_ws/src/vehicle_simulation_packages/air_sim/models/* /root/.gazebo/models 

RUN cp ros2_ws/src/vehicle_simulation_packages/air_description/urdf/sensors/VLP-16.urdf.xacro /opt/ros/iron/share/velodyne_description/urdf/

RUN echo "#!/bin/bash" > entrypoint.sh \
    && echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> entrypoint.sh \
    && echo "source /home/nav/ros2_ws/install/setup.bash" >> entrypoint.sh \
    && echo "exec \"\$@\"" >> entrypoint.sh \
    && sudo chmod +x entrypoint.sh \
    && echo "source /home/nav/entrypoint.sh" >> /root/.bashrc


ENTRYPOINT ["/home/nav/entrypoint.sh"]


CMD ["/bin/bash"]
