from setuptools import setup
import os
from glob import glob

package_name = 'waiter_brain_sdk'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.json')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mutabar',
    maintainer_email='tj907537572@mail.com',
    description='Universal multilingual AI brain for service robots',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'waiter_brain_node = waiter_brain_sdk.waiter_brain_node:main',
        ],
    },
)
