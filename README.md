<div align="center">
  <h1 align="center"> pika_ros </h1>
  <h3 align="center"> Agilex Robotics </h3>
  <p align="center">
    <a href="README.md"> English </a> | <a>中文</a> 
  </p>
</div>
<div align="center">

![ubuntu](https://img.shields.io/badge/Ubuntu-22.04-orange.svg)
![ROS2](https://img.shields.io/badge/ROS-humble-blue.svg)

</div>

## Introduction

Pika Data Suite (Pika) is a spatial data acquisition product for embodied AI data collection. It provides a portable, lightweight, all-in-one solution for general-purpose manipulation. The system consists of the acquisition device, model inference executor, localization base stations, and a data backpack. It supports efficient, accurate, and lightweight collection of robot spatial manipulation data.

Pika offers millimeter-level spatial information acquisition, supporting six-DoF pose, depth, ultra-wide-angle RGB, and gripper signals to meet multi-modal data collection needs in embodied AI. The executor can leverage collected data for model inference.

If you have any questions, suggestions, or feedback, please contact us via:

- GitHub Issues: https://github.com/agilexrobotics/pika_ros/issues
- Email: [support@agilex.ai](mailto:support@agilex.ai)

Our technical team will respond as soon as possible and provide support.

pika sdk: https://github.com/agilexrobotics/pika_sdk

pika teleoperation: https://github.com/agilexrobotics/PikaAnyArm

For more information, see the Pika Product User Manual (CN) and PIKA FAQ (CN).

## Supported Platforms

### Software

- Architecture: x86_64
- OS: Ubuntu 22.04
- ROS: humble


## Quick Start Links

- PikaSense setup and data collection: see `SETUP.md` (clone/build, device IDs, launch, record).
- Optional HTC Vive tracking in RViz (Steam-free at runtime): also in `SETUP.md` → “Optional: HTC Vive tracking in RViz”.

### TL;DR Vive + ROS 2

1) Pair tracker once in SteamVR (then close SteamVR).
2) Install udev rules, replug dongle.
3) Build/run Vive TF bridge:
```bash
cd ~/ros2_ws/src && git clone https://github.com/asymingt/libsurvive_ros2.git
cd ~/ros2_ws && rosdep update && rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select libsurvive_ros2 && source ~/ros2_ws/install/setup.bash
ros2 launch libsurvive_ros2 libsurvive_ros2.launch.py
```
4) RViz: Fixed Frame = parent from `/tf` (e.g., `libsurvive_world`); add TF.


