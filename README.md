# 🤖 SmartRobotBrain: Multilingual AI Brain for Restaurant Service Robots (ROS2)



![CI](https://github.com/tj907537572-spec/Smart-Waiter-AI/actions/workflows/ci.yml/badge.svg)




![ROS2 Humble](https://img.shields.io/badge/ROS2-Humble-blue)




![Python 3.10](https://img.shields.io/badge/Python-3.10-green)




![License MIT](https://img.shields.io/badge/License-MIT-yellow)



A modular ROS2 software layer that lets restaurant service robots talk to guests in **Tajik, Russian, English and Chinese**. It is built for Central Asian restaurants, where most robots on the market do not speak the local languages.

## Why

Service robots (Pudu, Keenon and similar) are already arriving in Central Asia, but their software supports few local languages. SmartRobotBrain adds localized voice, menus and order handling on top of the robot hardware.

## Features

- 🗣 Multilingual voice interaction: Tajik, Russian, English, Chinese
- 🍽 Menu in four languages with categories and upsell suggestions
- 🧭 Navigation to tables via Nav2
- 🤖 Tray control (servo) and battery management
- 👨‍🍳 Kitchen display for incoming orders
- 🔄 State machine for the full service flow

## Modules

| File | Purpose |
|------|---------|
| `nav2_client.py` | Navigation (Nav2) |
| `tts_node.py` | Speech output (Piper TTS) |
| `asr_node.py` | Speech input (Whisper ASR) |
| `tray_controller.py` | Tray (servo) |
| `battery_manager.py` | Battery monitoring |
| `kitchen_display.py` | Kitchen order screen |

## Quick start

```bash
# ROS2 Humble required
mkdir -p ~/ws/src
git clone https://github.com/tj907537572-spec/Smart-Waiter-AI.git ~/ws/src/waiter_brain_sdk
cd ~/ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## Project status

- ✅ Builds automatically as a ROS2 package (see the CI badge)
- 🔧 Unit tests are being added
- 🔧 Integration with real robot hardware is in progress
- 📌 This repository is the public part of the project. The full core is available to partners and investors on request.

## Partnership

We are looking for:
- **Robot distributors** who want local-language support for their robots
- **Restaurants** willing to run a pilot
- **Investors** interested in service robotics in Central Asia

Contact: Telegram: https://t.me/Yusuf200fg

## Languages

🇷🇺 Универсальный робот-официант на ROS2. Работает на таджикском, русском, английском и китайском.
🇹🇯 Робот-официант ба забонҳои тоҷикӣ, русӣ, англисӣ ва чинӣ.

## License

MIT
