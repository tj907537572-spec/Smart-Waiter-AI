#!/usr/bin/env python3
"""
🔋 BATTERY MANAGER v3.1 — SmartWaiter
Мониторинг батареи + автозарядка
Топики: /battery_level → /nav_goal
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
import time
from collections import deque
from pathlib import Path


class BatteryManager(Node):

    def __init__(self):
        super().__init__('battery_manager')
        self.get_logger().info("🔋 Battery Manager v3.1...")

        self.declare_parameter('low_threshold',      20.0)
        self.declare_parameter('critical_threshold', 10.0)
        self.declare_parameter('check_interval',     30.0)

        self.low_thr  = self.get_parameter('low_threshold').value
        self.crit_thr = self.get_parameter('critical_threshold').value

        self._history     = deque(maxlen=5)
        self.is_charging  = False
        self._last_warn   = 0.0

        self.pub_bat    = self.create_publisher(
            Float32, '/battery_level', 10
        )
        self.pub_nav    = self.create_publisher(
            String, '/nav_goal', 10
        )
        self.pub_speech = self.create_publisher(
            String, '/robot/speech', 10
        )

        self.create_timer(
            self.get_parameter('check_interval').value,
            self._check
        )
        self.get_logger().info("✅ Battery Manager готов!")

    def _check(self):
        raw = self._read()
        self._history.append(raw)
        level = sum(self._history) / len(self._history)

        msg = Float32()
        msg.data = float(level)
        self.pub_bat.publish(msg)
        self.get_logger().info(f"🔋 Батарея: {level:.1f}%")

        now = time.time()
        if level <= self.crit_thr and not self.is_charging:
            self.is_charging = True
            self._speak("🚨 Критический заряд! Еду на зарядку!")
            self._navigate("charging")
        elif level <= self.low_thr and not self.is_charging:
            if now - self._last_warn > 120.0:
                self._last_warn = now
                self._speak("⚠️ Низкий заряд батареи.")
        elif level >= 95.0 and self.is_charging:
            self.is_charging = False
            self._speak("🔋 Зарядка завершена! Готов к работе!")

    def _read(self) -> float:
        for path in ['/sys/class/power_supply/BAT0/capacity',
                     '/sys/class/power_supply/BAT1/capacity']:
            try:
                return float(Path(path).read_text().strip())
            except Exception:
                pass
        try:
            import board, busio, adafruit_ina219
            i2c = busio.I2C(board.SCL, board.SDA)
            ina = adafruit_ina219.INA219(i2c)
            v   = ina.bus_voltage + ina.shunt_voltage / 1000.0
            pct = (v - 9.0) / (12.6 - 9.0) * 100.0
            return max(0.0, min(100.0, pct))
        except Exception:
            pass
        if not hasattr(self, '_sim'):
            self._sim = 100.0
        self._sim = max(0.0, self._sim - 0.1)
        return self._sim

    def _navigate(self, target: str):
        msg = String()
        msg.data = target
        self.pub_nav.publish(msg)

    def _speak(self, text: str):
        msg = String()
        msg.data = text
        self.pub_speech.publish(msg)


def main():
    rclpy.init()
    node = BatteryManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
