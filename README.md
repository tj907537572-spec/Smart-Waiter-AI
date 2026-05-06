# Robot Waiter AI Brain (ROS 2)
This is a professional AI-core for service robots.

## Features:
- Multi-language support (Tajik, Russian, English)
- Obstacle avoidance logic
- AI-powered menu recommendations

## Licensing:
For the full source code and commercial license, contact: tj907537572@mail.com
---

## 🛠 Installation & Quick Start

This package is designed for **ROS 2 (Humble/Foxy)**. 

### 1. Clone the repository
Go to your ROS 2 workspace `src` folder and clone this SDK:
```bash
cd ~/ros2_ws/src
git clone [https://github.com/tj907537572-spec/Smart-Waiter-AI.git](https://github.com/tj907537572-spec/Smart-Waiter-AI.git)
cd ~/ros2_ws
colcon build --packages-select waiter_brain_sdk
source install/setup.bash
ros2 launch waiter_brain_sdk waiter_brain.launch.py region:=tj
ros2 topic pub /order std_msgs/msg/String "data: 'плов'"
