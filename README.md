# 🤖 SmartRobotBrain — Universal AI Waiter Robot (ROS2)



![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)




![Python](https://img.shields.io/badge/Python-3.10-green)




![License](https://img.shields.io/badge/License-MIT-yellow)



## 🌟 Описание

Универсальный робот-официант на ROS2.
Работает на 4 языках: 🇹🇯 Таджикский | 🇷🇺 Русский | 🇬🇧 English | 🇨🇳 中文

## 📦 Файлы проекта

| Файл | Описание |
|------|----------|
| `nav2_client.py` | 🗺️ Навигация (Nav2) |
| `tts_node.py` | 🔊 Голос (Piper TTS) |
| `asr_node.py` | 🎤 Слух (Whisper ASR) |
| `tray_controller.py` | 🍽️ Поднос (Servo) |
| `battery_manager.py` | 🔋 Батарея |
| `kitchen_display.py` | 🍳 Экран кухни |

## 🚀 Быстрый старт

### Установка
```bash
# ROS2 Humble
sudo apt install ros-humble-desktop ros-humble-nav2-bringup

# Python
pip install faster-whisper piper-tts pyaudio pyyaml
