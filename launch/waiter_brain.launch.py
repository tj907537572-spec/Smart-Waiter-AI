from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('region', default_value='tj'),
        Node(
            package='waiter_brain_sdk',
            executable='waiter_brain_node',
            output='screen',
            parameters=[{'region': LaunchConfiguration('region'), 'safety_dist': 0.7}]
        )
    ])
