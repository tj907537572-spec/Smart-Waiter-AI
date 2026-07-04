#!/usr/bin/env python3
"""
🚀 ROBOT WAITER LAUNCH v3.1
Запуск всех публичных нод
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    sim_time = LaunchConfiguration('sim_time', default='false')

    nav2_client = Node(
        package='waiter_brain_sdk',
        executable='nav2_client',
        name='nav2_client',
        output='screen',
        parameters=[{'use_sim_time': sim_time}],
        respawn=True,
        respawn_delay=3.0,
    )

    tts = Node(
        package='waiter_brain_sdk',
        executable='tts_node',
        name='tts_node',
        output='screen',
        parameters=[{
            'use_sim_time': sim_time,
            'models_dir': os.path.expanduser('~/models/tts'),
            'play_command': 'aplay',
        }],
        respawn=True,
        respawn_delay=3.0,
    )

    asr = Node(
        package='waiter_brain_sdk',
        executable='asr_node',
        name='asr_node',
        output='screen',
        parameters=[{
            'use_sim_time': sim_time,
            'model_size': 'base',
        }],
        respawn=True,
        respawn_delay=5.0,
    )

    tray = Node(
        package='waiter_brain_sdk',
        executable='tray_controller',
        name='tray_controller',
        output='screen',
        respawn=True,
        respawn_delay=2.0,
    )

    battery = Node(
        package='waiter_brain_sdk',
        executable='battery_manager',
        name='battery_manager',
        output='screen',
        parameters=[{
            'check_interval':     30.0,
            'low_threshold':      20.0,
            'critical_threshold': 10.0,
        }],
        respawn=True,
        respawn_delay=2.0,
    )

    kitchen = Node(
        package='waiter_brain_sdk',
        executable='kitchen_display',
        name='kitchen_display',
        output='screen',
        parameters=[{'port': 8081}],
        respawn=True,
        respawn_delay=2.0,
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'sim_time',
            default_value='false',
            description='Use simulation time'
        ),
        LogInfo(msg="🚀 SmartWaiter v3.1 запускается..."),
        nav2_client,
        tts,
        asr,
        tray,
        battery,
        kitchen,
    ])
