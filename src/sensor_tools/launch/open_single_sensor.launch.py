import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch import LaunchContext


def generate_launch_description():

    declared_arguments = [
        DeclareLaunchArgument('camera_ns', default_value=''),
        DeclareLaunchArgument('leader_ns', default_value=''),
        DeclareLaunchArgument('serial_no', default_value=''),
        DeclareLaunchArgument('camera_name', default_value='camera'),
        DeclareLaunchArgument('camera_fps', default_value='30'),
        DeclareLaunchArgument('camera_height', default_value='480'),
        DeclareLaunchArgument('camera_width', default_value='640'),
        DeclareLaunchArgument('camera_profile', default_value='640x480x30'),
        DeclareLaunchArgument('fisheye_port', default_value='22'),
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB22'),
        DeclareLaunchArgument('joint_name', default_value='center_joint')
    ]

    camera_ns = LaunchConfiguration('camera_ns')
    leader_ns = LaunchConfiguration('leader_ns')
    serial_no = LaunchConfiguration('serial_no')
    camera_name = LaunchConfiguration('camera_name')
    camera_fps = LaunchConfiguration('camera_fps')
    camera_height = LaunchConfiguration('camera_height')
    camera_width = LaunchConfiguration('camera_width')
    camera_profile = LaunchConfiguration('camera_profile')
    fisheye_port = LaunchConfiguration('fisheye_port')
    serial_port = LaunchConfiguration('serial_port')
    joint_name = LaunchConfiguration('joint_name')

    depth_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')]),
        launch_arguments={'serial_no': serial_no,
                          'camera_namespace': camera_ns,
                          'camera_name': camera_name,
                          'depth_module.color_profile': camera_profile, 
                          'depth_module.depth_profile': camera_profile,
                          'depth_module.infra_profile': camera_profile}.items()
    )

    return LaunchDescription(declared_arguments+[
        depth_camera_launch,
        Node(
            package='sensor_tools',
            executable='usb_camera.py',
            name='camera_fisheye',
            parameters=[{'camera_port': fisheye_port,
                         'camera_fps': camera_fps,
                         'camera_height': camera_height,
                         'camera_width': camera_width,
                         'camera_frame_id': [camera_ns, TextSubstitution(text="/camera_fisheye_link")] }],
            remappings=[
                ('/camera_rgb/color/image_raw', [camera_ns, TextSubstitution(text='/fisheye/color/image_raw')]),
                ('/camera_rgb/color/camera_info', [camera_ns, TextSubstitution(text='/fisheye/color/camera_info')])
            ],
            respawn=True,
            output='screen'
        ),
        Node(
            package='sensor_tools',
            executable='serial_gripper_imu',
            name='serial_gripper_imu',
            parameters=[{'serial_port': serial_port,
                         'joint_name': joint_name}],
            remappings=[
                ('/imu/data', [leader_ns, TextSubstitution(text='/imu/data')]),
                ('/gripper/data', [leader_ns, TextSubstitution(text='/pika/gripper/data')]),
                ('pika/gripper/data', [leader_ns, TextSubstitution(text='/pika/gripper/data')]),
                ('/gripper/ctrl', [leader_ns, TextSubstitution(text='/gripper/ctrl')]),
                ('/gripper/joint_state', [leader_ns, TextSubstitution(text='/gripper/joint_state')]),
                ('/gripper/joint_state_ctrl', [leader_ns, TextSubstitution(text='/joint_states')]),
                ('/joint_state_info', '/joint_states'),
                ('/joint_state_gripper', '/joint_states_gripper'),
                ('/data_capture_status', '/data_tools_dataCapture/status'),
                ('/teleop_status', '/teleop_status'),
                ('/localization_status', '/pika_localization_status'),
                ('/arm_control_status', '/arm_control_status'),
            ],
            respawn=True,
            output='screen'
        )
    ])
