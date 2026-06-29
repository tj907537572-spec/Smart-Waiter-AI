#!/usr/bin/env python3
"""
🤖 ROBOT WAITER BRAIN NODE v3.1
SmartRobotBrain - Universal AI Service Platform (ROS2)
4 языка: TJ / RU / EN / ZH
"""

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from std_msgs.msg import String, Bool, Float32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry

import json
import yaml
import sqlite3
import math
import random
import threading
import time
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from pathlib import Path


class RobotState(Enum):
    IDLE         = "idle"
    GREETING     = "greeting"
    TAKING_ORDER = "taking_order"
    NAVIGATING   = "navigating"
    DELIVERING   = "delivering"
    RETURNING    = "returning"
    CHARGING     = "charging"
    EMERGENCY    = "emergency"


class Language(Enum):
    TJ = "tj"
    RU = "ru"
    EN = "en"
    ZH = "zh"


def detect_language(text: str) -> str:
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return 'zh'
    tajik = {'салом','хуш','ташаккур','лутфан',
              'бубахшед','ман','мо','шумо','хайр'}
    if set(text.lower().split()) & tajik:
        return 'tj'
    first = text.strip().split()[0] if text.strip() else ''
    if first and all(ord(c) < 128 for c in first):
        return 'en'
    return 'ru'


class Phrases:
    DB = {
        "greeting": {
            "tj": "🙏 Ассалому алейкум! Хуш омадед!",
            "ru": "🙏 Добро пожаловать! Рады видеть вас!",
            "en": "🙏 Welcome! Wonderful to have you here!",
            "zh": "🙏 欢迎光临！很高兴见到您！",
        },
        "farewell": {
            "tj": "👋 Ташаккур! Боз биёед!",
            "ru": "👋 Спасибо! Приходите снова!",
            "en": "👋 Thank you! Please come again!",
            "zh": "👋 谢谢！欢迎再次光临！",
        },
        "offer_menu": {
            "tj": "📋 Марҳамат, менюи мо!",
            "ru": "📋 Позвольте предложить наше меню!",
            "en": "📋 Please allow me to present our menu!",
            "zh": "📋 请允许我为您介绍菜单！",
        },
        "order_accepted": {
            "tj": "✅ Ба ошхона фиристодам. 15-20 дақиқа.",
            "ru": "✅ Заказ передан на кухню. 15-20 минут.",
            "en": "✅ Order sent to kitchen. 15-20 minutes.",
            "zh": "✅ 订单已发送至厨房。15-20分钟。",
        },
        "delivering": {
            "tj": "🍽️ Фармоиши шумо тайёр! Ноши ҷон!",
            "ru": "🍽️ Ваш заказ готов! Приятного аппетита!",
            "en": "🍽️ Your order is ready! Bon appétit!",
            "zh": "🍽️ 您的菜来了！请慢用！",
        },
        "low_battery": {
            "tj": "🔋 Батарея кам. Барои зарядгирӣ меравам.",
            "ru": "🔋 Заряд заканчивается. Иду на зарядку.",
            "en": "🔋 Battery low. Going to charge.",
            "zh": "🔋 电量不足。去充电。",
        },
        "unknown": {
            "tj": "🤔 Нафаҳмидам. Гӯед: меню, фармоиш, хайр.",
            "ru": "🤔 Не понял. Скажите: меню, заказ, до свидания.",
            "en": "🤔 Sorry. Say: menu, order, or goodbye.",
            "zh": "🤔 没听懂。请说：菜单、点餐或再见。",
        },
    }

    @classmethod
    def get(cls, key: str, lang: str) -> str:
        entry = cls.DB.get(key, {})
        return entry.get(lang) or entry.get("ru", f"[{key}]")


class BrainNode(Node):

    def __init__(self):
        super().__init__('robot_waiter_brain')
        self.get_logger().info("🤖 SmartRobotBrain v3.1 запускается...")

        self._state_lock = threading.Lock()
        self._cb_group   = ReentrantCallbackGroup()

        # Состояние
        self._state         = RobotState.IDLE
        self.language       = Language.RU
        self.battery_level  = 100.0
        self.current_table: Optional[int] = None
        self.current_order: Optional[str] = None
        self.nav_retry      = 0

        # Publishers
        self.pub_speech  = self.create_publisher(String, '/robot/speech',   10)
        self.pub_face    = self.create_publisher(String, '/robot/face',     10)
        self.pub_nav     = self.create_publisher(String, '/nav_goal',       10)
        self.pub_tray    = self.create_publisher(String, '/tray_command',   10)
        self.pub_cmdvel  = self.create_publisher(Twist,  '/cmd_vel',        10)

        # Subscribers
        kw = {"callback_group": self._cb_group}
        self.create_subscription(String,    '/voice_command',       self._cb_voice,   10, **kw)
        self.create_subscription(String,    '/robot/button_press',  self._cb_button,  10, **kw)
        self.create_subscription(String,    '/kitchen/order_ready', self._cb_kitchen, 10, **kw)
        self.create_subscription(String,    '/nav_status',          self._cb_nav,     10, **kw)
        self.create_subscription(Bool,      '/tray_status',         self._cb_tray,    10, **kw)
        self.create_subscription(Float32,   '/battery_level',       self._cb_battery, 10, **kw)
        self.create_subscription(LaserScan, '/scan',                self._cb_lidar,   10, **kw)

        self.create_timer(60.0, self._battery_check)

        self.get_logger().info("✅ SmartRobotBrain v3.1 готов!")
        self._speak("Система активирована. Робот-официант готов!", "ru")
        self._face("😊")

    @property
    def state(self):
        with self._state_lock:
            return self._state

    @state.setter
    def state(self, v):
        with self._state_lock:
            old = self._state
            self._state = v
        if old != v:
            self.get_logger().info(f"🔄 {old.value} → {v.value}")

    # ── Callbacks ──────────────────────────────

    def _cb_voice(self, msg: String):
        text = msg.data.strip()
        if not text:
            return
        self.language = Language(detect_language(text))
        self.get_logger().info(f"🎤 [{self.language.value}]: {text}")
        self._process(text.lower())

    def _cb_button(self, msg: String):
        self._process(msg.data.strip().lower())

    def _cb_kitchen(self, msg: String):
        try:
            data = json.loads(msg.data)
        except Exception:
            return
        self.current_order = data.get("order_id")
        self.current_table = data.get("table_id")
        self.state = RobotState.DELIVERING
        lang = self.language.value
        self._speak(Phrases.get("delivering", lang), lang)
        self._navigate("kitchen")

    def _cb_nav(self, msg: String):
        try:
            data = json.loads(msg.data)
        except Exception:
            return
        status = data.get("status", "")
        target = data.get("target", "")
        if status == "SUCCEEDED":
            self.nav_retry = 0
            self._on_arrival(target)
        elif status in ("ABORTED", "FAILED"):
            self.nav_retry += 1
            if self.nav_retry < 3:
                time.sleep(2)
                self._navigate(target)
            else:
                self.nav_retry = 0
                self.state = RobotState.IDLE
                self._speak("Не удалось добраться.", "ru")

    def _cb_tray(self, msg: Bool):
        pass  # используется в safety

    def _cb_battery(self, msg: Float32):
        self.battery_level = msg.data
        if self.battery_level <= 10.0 and self.state != RobotState.CHARGING:
            self.state = RobotState.CHARGING
            lang = self.language.value
            self._speak(Phrases.get("low_battery", lang), lang)
            self._navigate("charging")

    def _cb_lidar(self, msg: LaserScan):
        ranges = [r for r in msg.ranges
                  if 0.05 < r < 10.0
                  and not math.isinf(r)
                  and not math.isnan(r)]
        if not ranges:
            return
        min_d = min(ranges)
        if min_d < 0.30 and self.state != RobotState.EMERGENCY:
            self.state = RobotState.EMERGENCY
            self.pub_cmdvel.publish(Twist())
            self._speak("⛔ Внимание! Экстренная остановка!", "ru")
            self._face("😰")
        elif min_d > 1.20 and self.state == RobotState.EMERGENCY:
            self.state = RobotState.IDLE
            self._face("😊")

    def _battery_check(self):
        if self.battery_level <= 20.0 and self.state not in (
            RobotState.CHARGING, RobotState.EMERGENCY
        ):
            lang = self.language.value
            self._speak(Phrases.get("low_battery", lang), lang)
            self.state = RobotState.CHARGING
            self._navigate("charging")

    # ── Команды ────────────────────────────────

    _GREET   = {'привет','hello','salom','салом','ассалом','你好'}
    _MENU    = {'меню','menu','менюи','菜单'}
    _ORDER   = {'заказ','заказать','order','фармоиш','点餐'}
    _DELIVER = {'принести','deliver','оварданд','上菜'}
    _BILL    = {'счёт','счет','bill','ҳисоб','买单'}
    _BYE     = {'до свидания','пока','goodbye','хайр','再见'}
    _JOKE    = {'шутка','joke','ҳазл','笑话'}

    def _process(self, cmd: str):
        lang  = self.language.value
        words = set(cmd.split())

        if words & self._GREET:
            self._speak(Phrases.get("greeting", lang), lang)
            self._face("😊")
        elif words & self._MENU:
            self._speak(Phrases.get("offer_menu", lang), lang)
            self._face("📋")
        elif words & self._ORDER:
            self._do_order()
        elif cmd.startswith("add:"):
            self._speak(f"✅ Добавлено в заказ!", "ru")
        elif words & self._DELIVER:
            self._navigate(f"table_{self.current_table or 1}")
        elif words & self._BILL:
            self._speak("🧾 Сейчас принесу счёт!", lang)
            self._face("🧾")
        elif words & self._BYE:
            self._speak(Phrases.get("farewell", lang), lang)
            self._face("👋")
            self.state = RobotState.RETURNING
            self._navigate("base")
        elif words & self._JOKE:
            jokes = {
                "ru": "😄 Почему я лучший официант? Никогда не устаю!",
                "tj": "😄 Чаро ман беҳтаринам? Ҳеҷ гоҳ хаста намешавам!",
                "en": "😄 Why am I perfect? I never get tired!",
                "zh": "😄 为什么我最好？我永不疲倦！",
            }
            self._speak(jokes.get(lang, jokes["ru"]), lang)
            self._face("😄")
        elif cmd.startswith("go:"):
            self._navigate(cmd.split(":", 1)[1].strip())
        elif cmd.startswith("table:"):
            try:
                self.current_table = int(cmd.split(":", 1)[1])
                self._speak(f"Стол №{self.current_table}", "ru")
            except ValueError:
                pass
        else:
            self._speak(Phrases.get("unknown", lang), lang)
            self._face("🤔")

    def _do_order(self):
        lang = self.language.value
        self.state = RobotState.TAKING_ORDER
        self._speak(Phrases.get("order_accepted", lang), lang)
        self._face("📝")

    def _on_arrival(self, target: str):
        lang = self.language.value
        if target.startswith("table_"):
            tid = target.split("_")[1]
            msgs = {
                "ru": f"🍽️ Доставлено к столу №{tid}! Приятного аппетита!",
                "tj": f"🍽️ Ба мизи №{tid} расондам! Ноши ҷон!",
                "en": f"🍽️ Delivered to table {tid}! Enjoy!",
                "zh": f"🍽️ 已送达第{tid}桌！请慢用！",
            }
            self._speak(msgs.get(lang, msgs["ru"]), lang)
            self._face("🍽️")
            self._tray("OPEN")
        elif target == "kitchen":
            self._speak("🍳 Я на кухне!", "ru")
            self._tray("LOAD")
        elif target == "base":
            self._speak("🏠 Я на базе. Готов!", "ru")
            self._face("😊")
        elif target == "charging":
            self._face("🔋")
        self.state = RobotState.IDLE

    # ── Helpers ────────────────────────────────

    def _speak(self, text: str, lang: str):
        msg = String()
        msg.data = text
        self.pub_speech.publish(msg)
        self.get_logger().info(f"🔊 {text}")

    def _face(self, emoji: str):
        msg = String()
        msg.data = emoji
        self.pub_face.publish(msg)

    def _navigate(self, target: str):
        self.state = RobotState.NAVIGATING
        msg = String()
        msg.data = target
        self.pub_nav.publish(msg)
        self.get_logger().info(f"🚶 → {target}")

    def _tray(self, cmd: str):
        msg = String()
        msg.data = cmd
        self.pub_tray.publish(msg)


def main():
    rclpy.init()
    node = BrainNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
    
