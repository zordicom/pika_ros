#!/usr/bin/env python3

import subprocess
import re
import os
import cv2
import time

def run_command(command):
    """Run a command and return its output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return None


def get_device_info():
    """Get device information"""
    # Run rs-enumerate-devices
    rs_output = run_command("rs-enumerate-devices -s")
    if not rs_output:
        print("Failed to get depth camera data")
        return None, None

    # Parse output to obtain serial number
    serial_match = re.search(r'Intel RealSense D405\s+(\d+)', rs_output)
    if not serial_match:
        print("Failed to get depth camera data")
        return None, None
    serial_number = serial_match.group(1)

    # Run udevadm
    ls_output = run_command("ls /dev | grep ttyUSB | grep -v ttyUSB50 | grep -v ttyUSB51 | grep -v ttyUSB60 | grep -v ttyUSB61")
    count = ls_output.count("tty")
    if count > 1:
        print("Please ensure only one USB serial device is connected")
        return None, None
    udev_output = run_command(f"udevadm info /dev/{ls_output} | grep DEVPATH")
    if not udev_output:
        print("Failed to get serial port info")
        return None, None

    # Parse USB path (format like 1-13.2.4:1.0)
    usb_path = udev_output[:udev_output.find(ls_output)][:-1]
    usb_path = usb_path[usb_path.rfind("/")+1:]
    print("Find fisheye camera: press 's' when a fisheye camera appears, press 'q' for non-fisheye (press in the image window, not in the terminal!)")
    video_path = None
    cv2.setLogLevel(0)
    for i in range(50):
        cap = cv2.VideoCapture(i)
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        key = None
        if cap.isOpened():
            # print("port:", "/dev/video"+str(i))
            while True:
                ret, frame = cap.read()
                cv2.imshow("/dev/video"+str(i), frame)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break
                elif key & 0xFF == ord('s'):
                    break
        cv2.destroyAllWindows()
        if key is not None and key & 0xFF == ord('s'):
            video_path = 'video' + str(i)
            break
    cv2.destroyAllWindows()
    if video_path is None:
        print("Failed to get fisheye camera data")
        return None, None
    udev_output = run_command(f"udevadm info /dev/{video_path} | grep DEVPATH")
    video_path = udev_output[:udev_output.find("video")][:-1]  # format like 1-13.2.4:1.0
    video_path = video_path[video_path.rfind("/")+1:]

    return serial_number, usb_path, video_path


def generate_setup_bash(left_info, right_info, select):
    if select == "1":
        path = "setup_multi_sensor.bash"
        usb_num1 = 50
        usb_num2 = 51
        name1 = "sensor_"
        name2 = "sensor_"
        to1 = ">"
        to2 = ">>"
    if select == "2":
        path = "setup_multi_gripper.bash"
        usb_num1 = 60
        usb_num2 = 61
        name1 = "gripper_"
        name2 = "gripper_"
        to1 = ">"
        to2 = ">>"
    if select == "3":
        path = "setup_sensor_gripper.bash"
        usb_num1 = 50
        usb_num2 = 60
        name1 = "sensor_"
        name2 = "gripper_"
        to1 = ">"
        to2 = ">"
    """Generate setup.bash file"""
    content = f"""
#/bin/bash

sudo sh -c 'echo "ACTION==\\"add\\", KERNELS==\\"{left_info[1]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"ttyUSB{usb_num1}\\"" {to1} /etc/udev/rules.d/{name1}serial.rules'
sudo sh -c 'echo "ACTION==\\"add\\", KERNELS==\\"{right_info[1]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"ttyUSB{usb_num2}\\"" {to2} /etc/udev/rules.d/{name2}serial.rules'

sudo sh -c 'echo "ACTION==\\"add\\", KERNEL==\\"video[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48]*\\", KERNELS==\\"{left_info[2]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"video{usb_num1}\\"" {to1} /etc/udev/rules.d/{name1}fisheye.rules'
sudo sh -c 'echo "ACTION==\\"add\\", KERNEL==\\"video[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48]*\\", KERNELS==\\"{right_info[2]}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"video{usb_num2}\\"" {to2} /etc/udev/rules.d/{name2}fisheye.rules'

sudo udevadm control --reload-rules && sudo service udev restart && sudo udevadm trigger
               """
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)


def generate_start_bash(left_info, right_info, select):
    if select == "1":
        path = "start_multi_sensor.bash"
        usb_num1 = 50
        usb_num2 = 51
        content = f"""
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
camera_fps=30
camera_width=640
camera_height=480
l_depth_camera_no={left_info[0]}
r_depth_camera_no={right_info[0]}

l_serial_port=/dev/ttyUSB{usb_num1}
r_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
l_fisheye_port={usb_num1}
r_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/humble/setup.bash && cd $SCRIPT_DIR/../install/sensor_tools/share/sensor_tools/scripts/ && chmod 777 usb_camera.py
if [ -n "$1" ]; then
    source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_multi_sensor.launch.py l_depth_camera_no:=_$l_depth_camera_no r_depth_camera_no:=_$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps name:=$1 name_index:=$1_
else
    source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_multi_sensor.launch.py l_depth_camera_no:=_$l_depth_camera_no r_depth_camera_no:=_$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps
fi
                """
    if select == "2":
        path = "start_multi_gripper.bash"
        usb_num1 = 60
        usb_num2 = 61
        content = f"""
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
camera_fps=30
camera_width=640
camera_height=480
l_depth_camera_no={left_info[0]}
r_depth_camera_no={right_info[0]}

l_serial_port=/dev/ttyUSB{usb_num1}
r_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
l_fisheye_port={usb_num1}
r_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/humble/setup.bash && cd $SCRIPT_DIR/../install/sensor_tools/share/sensor_tools/scripts/ && chmod 777 usb_camera.py
if [ -n "$1" ]; then
    source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_multi_gripper.launch.py l_depth_camera_no:=_$l_depth_camera_no r_depth_camera_no:=_$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps name:=$1 name_index:=$1_
else
    source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_multi_gripper.launch.py l_depth_camera_no:=_$l_depth_camera_no r_depth_camera_no:=_$r_depth_camera_no l_serial_port:=$l_serial_port r_serial_port:=$r_serial_port l_fisheye_port:=$l_fisheye_port r_fisheye_port:=$r_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps
fi
                """
    if select == "3":
        path = "start_sensor_gripper.bash"
        usb_num1 = 50
        usb_num2 = 60
        content = f"""
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
camera_fps=30
camera_width=640
camera_height=480
sensor_depth_camera_no={left_info[0]}
gripper_depth_camera_no={right_info[0]}

sensor_serial_port=/dev/ttyUSB{usb_num1}
gripper_serial_port=/dev/ttyUSB{usb_num2}
sudo chmod a+rw /dev/ttyUSB*
sensor_fisheye_port={usb_num1}
gripper_fisheye_port={usb_num2}
sudo chmod a+rw /dev/video*

source /opt/ros/humble/setup.bash && cd $SCRIPT_DIR/../install/sensor_tools/share/sensor_tools/scripts/ && chmod 777 usb_camera.py
source $SCRIPT_DIR/../install/setup.bash && ros2 launch sensor_tools open_sensor_gripper.launch.py sensor_depth_camera_no:=_$sensor_depth_camera_no gripper_depth_camera_no:=_$gripper_depth_camera_no sensor_serial_port:=$sensor_serial_port gripper_serial_port:=$gripper_serial_port sensor_fisheye_port:=$sensor_fisheye_port gripper_fisheye_port:=$gripper_fisheye_port camera_fps:=$camera_fps camera_width:=$camera_width camera_height:=$camera_height camera_profile:=$camera_width,$camera_height,$camera_fps
                """
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)


def main():
    print("=== Pika setup tool ===")
    select = None
    while True:
        select = input("Select binding\n1. Two pika sensors (handheld grippers)\n2. Two pika grippers (mounted on robot arm)\n3. One pika sensor and one pika gripper\nEnter choice: ")
        if select == "1":
            device1 = "left"
            device2 = "right"
            break
        if select == "2":
            device1 = "left"
            device2 = "right"
            break
        if select == "3":
            device1 = "sensor"
            device2 = "gripper"
            break
        else:
            print("Please enter 1, 2, or 3")
            continue

    print(f"Insert the {device1} device, then press Enter to continue...")
    input()
    print(f"Fetching {device1} device info...")
    while True:
        left_info = get_device_info()
        if not left_info[0]:
            print(f"Failed to get {device1} device info. Check connection and press Enter to continue...")
            input()
        else:
            break
    print(f"{device1} device info: {left_info[0]} {left_info[1]} {left_info[2]}")


    print(f"Unplug the {device1} device, plug in the {device2} device (do not use the same USB port; after configuration the USB port must remain the same), and press Enter to continue...")
    input()
    print(f"Fetching {device2} device info...")
    while True:
        right_info = get_device_info()
        if not right_info[0]:
            print(f"Failed to get {device2} device info. Check connection and press Enter to continue...")
            input()
        else:
            break
    print(f"{device2} device info: {right_info[0]} {right_info[1]} {right_info[2]}")

    # Generate configuration files
    generate_setup_bash(left_info, right_info, select)
    generate_start_bash(left_info, right_info, select)
    setup_path = "setup_multi_sensor.bash" if select=="1" else ("setup_multi_gripper.bash" if select=="2" else "setup_sensor_gripper.bash")
    start_path = "start_multi_sensor.bash" if select=="1" else ("start_multi_gripper.bash" if select=="2" else "start_sensor_gripper.bash")
    print("Configuration complete! Generated files:")
    print(f"1. {setup_path}")
    print(f"2. {start_path}")
    print(f"Executing {setup_path}")
    run_command(f"bash {setup_path}")
    print("Execution finished.")
    while True:
        print("Please replug the devices into the previously bound USB ports. Then press Enter to check if binding succeeded...")
        input()
        print("Please wait...")
        time.sleep(5)
        video_list = run_command("ls /dev | grep video")
        usb_list = run_command("ls /dev | grep ttyUSB")
        if (select == "1" or select == "3") and video_list.find("50") < 0:
            print("Missing sensor (left) fisheye")
            continue
        if (select == "1") and video_list.find("51") < 0:
            print("Missing sensor (right) fisheye")
            continue
        if (select == "2" or select == "3") and video_list.find("60") < 0:
            print("Missing gripper (left) fisheye")
            continue
        if (select == "2") and video_list.find("61") < 0:
            print("Missing gripper (right) fisheye")
            continue
        if (select == "1" or select == "3") and usb_list.find("50") < 0:
            print("Missing sensor (left) serial")
            continue
        if (select == "1") and usb_list.find("51") < 0:
            print("Missing sensor (right) serial")
            continue
        if (select == "2" or select == "3") and usb_list.find("60") < 0:
            print("Missing gripper (left) serial")
            continue
        if (select == "2") and usb_list.find("61") < 0:
            print("Missing gripper (right) serial")
            continue
        break
    print("Binding successful. To start devices:")
    print(f"2. Then run: bash {start_path}")


if __name__ == "__main__":
    main()
