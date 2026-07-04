#!/usr/bin/env python3
"""
🍽️ TRAY CONTROLLER v3.1 — SmartWaiter
Управление подносом (Servo/GPIO)
Команды: OPEN/CLOSE/LOAD/CLEAR
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool

try:
    from adafruit_servokit import ServoKit
    _HW = True
except ImportError:
    _HW = False


class TrayController(Node):

    ANGLE_CLOSED = 0
    ANGLE_LOAD   = 45
    ANGLE_OPEN   = 90

    def __init__(self):
        super().__init__('tray_controller')
        self.get_logger().info("🍽️ Tray Controller v3.1...")

        self.kit      = None
        self.srv_tray = None

        if _HW:
            try:
                self.kit      = ServoKit(channels=16)
                self.srv_tray = self.kit.servo[0]
                self.srv_tray.angle = self.ANGLE_CLOSED
                self.get_logger().info("✅ PCA9685 подключён")
            except Exception as e:
                self.get_logger().error(f"❌ Servo: {e}")
        else:
            self.get_logger().warn("⚠️ Симуляция сервопривода")

        self.position = "CLOSED"
        self.has_food = False

        self.pub_status = self.create_publisher(
            Bool, '/tray_status', 10
        )
        self.pub_speech = self.create_publisher(
            String, '/robot/speech', 10
        )
        self.create_subscription(
            String, '/tray_command', self._cb_cmd, 10
        )
        self.create_timer(2.0, self._pub_status_timer)
        self.get_logger().info("✅ Tray Controller готов!")

    def _cb_cmd(self, msg: String):
        cmd = msg.data.strip().upper()
        self.get_logger().info(f"📦 Поднос: {cmd}")

        if cmd == "OPEN":
            self._set(self.ANGLE_OPEN)
            self.position = "OPEN"
            self._speak("🍽️ Поднос открыт. Приятного аппетита!")
        elif cmd == "CLOSE":
            self._set(self.ANGLE_CLOSED)
            self.position = "CLOSED"
            self.has_food = True
        elif cmd == "LOAD":
            self._set(self.ANGLE_LOAD)
            self.position = "LOAD"
            self._speak("🍳 Готов к загрузке!")
        elif cmd == "CLEAR":
            self._set(self.ANGLE_CLOSED)
            self.position = "CLOSED"
            self.has_food = False
            self._speak("✅ Поднос пустой. Готов!")
        else:
            self.get_logger().warn(f"⚠️ Неизвестно: {cmd}")

    def _set(self, angle: int):
        if self.srv_tray is not None:
            self.srv_tray.angle = angle
        self.get_logger().info(f"🔧 Поднос → {angle}°")

    def _speak(self, text: str):
        msg = String()
        msg.data = text
        self.pub_speech.publish(msg)

    def _pub_status_timer(self):
        msg = Bool()
        msg.data = self.has_food
        self.pub_status.publish(msg)

    def destroy_node(self):
        if self.srv_tray is not None:
            try:
                self.srv_tray.angle = self.ANGLE_CLOSED
            except Exception:
                pass
        super().destroy_node()


def main():
    rclpy.init()
    node = TrayController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
