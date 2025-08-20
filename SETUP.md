# PikaSense setup
## Getting started (clone and build)

1) Create workspace and clone
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone <your_repo_url> pika_ros
# If submodules are used:
cd pika_ros
git submodule update --init --recursive
cd ..
```

2) Install dependencies
```bash
sudo apt update
rosdep update
rosdep install --from-paths . --ignore-src -r -y
```

3) Build minimal packages needed for PikaSense + data capture
```bash
cd ~/ros2_ws
colcon build --event-handlers console_direct+ --packages-select data_msgs sensor_tools data_tools realsense2_camera
source ~/ros2_ws/install/setup.bash
```

4) One-time permissions and (optional) udev rules
- Add yourself to dialout (log out/in once) or use temporary chmod
- Apply the udev rules shown below in “One-time setup”
Overview
- Run PikaSense (RealSense + fisheye), optional grippers, visualize, and record (MCAP or raw bag).
- RealSense SDK is optional. Install only if devices don’t enumerate.

## One-time setup
- Serial permissions (pick one):
```bash
sudo usermod -aG dialout $USER   # log out/in once
```
- Create data dir:
```bash
mkdir -p /home/zordi/data
```
- Udev rules (recommended)
```bash
# Create rules file
sudo tee /etc/udev/rules.d/60-pikasense.rules >/dev/null <<'RULES'
# Intel RealSense (vendor 8086) video nodes
SUBSYSTEM=="video4linux", ATTRS{idVendor}=="8086", MODE="0666"
# Sunplus fisheye (vendor 1bcf) video nodes
SUBSYSTEM=="video4linux", ATTRS{idVendor}=="1bcf", MODE="0666"
# CH340 USB-serial (gripper dongle)
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7522", MODE="0666"
RULES
# Reload rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```
- Optional: RealSense SDK/udev (only if needed)
```bash
sudo apt update
sudo apt install -y software-properties-common curl gnupg lsb-release
curl -fsSL https://librealsense.intel.com/Debian/IntelRealSense_pub.gpg | sudo gpg --dearmor -o /usr/share/keyrings/librealsense-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/librealsense-archive-keyring.gpg] https://librealsense.intel.com/Debian/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/librealsense.list
sudo apt update
sudo apt install -y librealsense2-dkms librealsense2-utils librealsense2-udev
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Start of each session
- Source env:
```bash
source ~/ros2_ws/install/setup.bash
```
- Detect devices:
```bash
# Fisheye indices (note which is L/R)
python3 $(ros2 pkg prefix sensor_tools)/share/sensor_tools/scripts/find_usb_camera.py

# RealSense serials (needed for dual)
rs-enumerate-devices | grep Serial
```

## Launch sensors
- Single device (no gripper):
```bash
ros2 launch sensor_tools open_single_sensor.launch.py \
  fisheye_port:=<IDX> \
  camera_profile:=640x480x30
```
- Two devices (dual). Quote serials as strings:
```bash
ros2 launch sensor_tools open_multi_sensor.launch.py \
  l_fisheye_port:=<L_IDX> r_fisheye_port:=<R_IDX> \
  l_depth_camera_no:="'<L_SERIAL>'" r_depth_camera_no:="'<R_SERIAL>'" \
  camera_profile:=640x480x15
```
- With grippers (optional): add `l_serial_port:=/dev/ttyUSB0 r_serial_port:=/dev/ttyUSB1`.

## Visualize
- Quick: `ros2 run rqt_image_view rqt_image_view`
- RViz: `rviz2` → Fixed Frame: `camera_link`
  - Image: `/camera(_l|_r)?/color/image_raw`, `/camera_fisheye_(l|r)/color/image_raw`
  - Optional PointCloud2: `/camera/depth/color/points` (enable below)

## Optional: HTC Vive tracking in RViz (Steam-free at runtime)

1) Pair once in SteamVR, then close SteamVR
- Install Steam → install “SteamVR” from the Store → launch it.
- Power base stations (LEDs green), plug watchman dongle, power Vive tracker.
- SteamVR → Devices → Pair Controller → Vive Tracker (hold the small triangular Pair button until it blinks blue). When the icon goes green, CLOSE SteamVR.

2) USB permissions (udev rules)
```bash
sudo curl -fsSL https://raw.githubusercontent.com/cntools/libsurvive/master/useful_files/81-vive.rules \
  -o /etc/udev/rules.d/81-vive.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```
Unplug/replug the dongle.

3) Install and run the Vive TF bridge
```bash
cd ~/ros2_ws/src
git clone https://github.com/asymingt/libsurvive_ros2.git
cd ~/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select libsurvive_ros2
source ~/ros2_ws/install/setup.bash
ros2 launch libsurvive_ros2 libsurvive_ros2.launch.py
```

4) Verify /tf and LHR frames
```bash
ros2 topic echo /tf --once | grep -m1 'frame_id:' | awk '{print $2}'
ros2 topic echo /tf --once | grep 'child_frame_id:' | head
```

5) RViz
- Fixed Frame: set to the parent from the first command (e.g., `libsurvive_world`). Add TF display; enable Names/Axes.

Tips
- Swap dongle ports safely (stop bridge → replug → relaunch). Orange LED = charging; unplug USB‑C to track.
- Multiple trackers: A single watchman dongle can technically pair with more than one tracker, but reliability is significantly better with one dongle per tracker. For dual PikaSense trackers, use two dongles.

## Record data
- MCAP (dated folder; dual config):
```bash
DATE=$(date +%Y%m%d_%H%M%S)
ros2 launch data_tools run_aloha_data_capture_to_mcap.launch.py \
  paramsFile:=/home/zordi/ros2_ws/src/pika_ros/src/data_tools/config/multi_pika_data_params.yaml \
  datasetDir:=/home/zordi/data/$DATE useService:=false hz:=20 timeout:=2
```
- Raw topics (dual; avoids depth compression warnings):
```bash
DATE=$(date +%Y%m%d_%H%M%S)
ros2 bag record -o /home/zordi/data/dual_${DATE} \
  /camera_l/color/image_raw /camera_l/color/camera_info \
  /camera_l/aligned_depth_to_color/image_raw /camera_l/aligned_depth_to_color/camera_info \
  /camera_r/color/image_raw /camera_r/color/camera_info \
  /camera_r/aligned_depth_to_color/image_raw /camera_r/aligned_depth_to_color/camera_info \
  /camera_fisheye_l/color/image_raw /camera_fisheye_l/color/camera_info \
  /camera_fisheye_r/color/image_raw /camera_fisheye_r/color/camera_info
```
- Optional point cloud (live):
```bash
ros2 param set /camera pointcloud.enable true
ros2 param set /camera align_depth true
```

## After recording
```bash
ros2 bag info /home/zordi/data/$DATE/episode0_0.mcap || true
```
Expect non-zero messages for color/depth/fisheye + camera_info; gripper topics if connected.

## Troubleshooting
- RealSense serial type invalid → quote strings:
```bash
l_depth_camera_no:="'2304...'" r_depth_camera_no:="'2303...'"
```
- “16UC1 is not a color format” spam → record raw depth (raw topics above), or use a PNG compressor if you need compressed depth.
- Fisheye “can’t open camera by index” → re-run finder; pass the correct integer `fisheye_port`.
- Bag shows 0 messages → keep recorder running until publishers start; verify with `ros2 topic list` and `ros2 topic hz`.
- USB bandwidth/drops (dual) → use 640x480x15; short USB3 cables; different USB3 controllers/ports.
- RealSense not enumerating:
```bash
sudo modprobe uvcvideo
lsusb -t | grep -E "5000M|SuperSpeed"
# disable autosuspend temporarily
echo -1 | sudo tee /sys/module/usbcore/parameters/autosuspend
# reload udev if you installed rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Notes
- Don’t run repo-local scripts from `src/`; use the launch commands above or installed scripts at:
$(ros2 pkg prefix sensor_tools)/share/sensor_tools/scripts/
EOF
