from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'waiter_brain_sdk'

setup(
    name=package_name,
    version='3.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            [f'resource/{package_name}']),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'),
            glob('config/*')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='SmartRobotBrain',
    maintainer_email='robot@smartwaiter.ai',
    description='Universal AI Waiter Robot v3.1',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'nav2_client     = waiter_brain_sdk.nav2_client:main',
            'tts_node        = waiter_brain_sdk.tts_node:main',
            'asr_node        = waiter_brain_sdk.asr_node:main',
            'tray_controller = waiter_brain_sdk.tray_controller:main',
            'battery_manager = waiter_brain_sdk.battery_manager:main',
            'kitchen_display = waiter_brain_sdk.kitchen_display:main',
        ],
    },
)
