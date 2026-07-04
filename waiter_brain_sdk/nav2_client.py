#!/usr/bin/env python3
"""
🗺️ NAV2 CLIENT v3.1 — SmartWaiter
Навигация робота через Nav2
Топики: /nav_goal → /nav_status
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import NavigateToPose
import yaml, math, json, threading
from typing import Dict, Optional


class Nav2ClientNode(Node):

    def __init__(self):
        super().__init__('nav2_client')
        self.get_logger().info("🗺️ Nav2 Client v3.1...")
        self._cb_group  = ReentrantCallbackGroup()
        self._goal_lock = threading.Lock()
        self.waypoints: Dict[str, dict] = {}
        self._load_waypoints()
        self.nav_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose',
            callback_group=self._cb_group
        )
        if self.nav_client.wait_for_server(timeout_sec=15.0):
            self.get_logger().info("✅ Nav2 подключён!")
        else:
            self.get_logger().error("❌ Nav2 недоступен!")
        self.pub_status = self.create_publisher(
            String, '/nav_status', 10
        )
        self.pub_speech = self.create_publisher(
            String, '/robot/speech', 10
        )
        self.pub_face = self.create_publisher(
            String, '/robot/face', 10
        )
        self.pub_tray = self.create_publisher(
            String, '/tray_command', 10
        )
        self.create_subscription(
            String, '/nav_goal', self._cb_goal, 10,
            callback_group=self._cb_group
        )
        self.current_target: Optional[str] = None
        self.goal_handle = None
        self._pending: Optional[str] = None
        self.get_logger().info("✅ Nav2 Client готов!")

    def _load_waypoints(self):
        try:
            with open('config/tables.yaml', 'r') as f:
                cfg = yaml.safe_load(f) or {}
            rest = cfg.get('restaurant', {})
            for name, d in rest.get('waypoints', {}).items():
                self.waypoints[name] = {
                    'x': float(d['x']),
                    'y': float(d['y']),
                    'theta': float(d.get('theta', 0.0))
                }
            for tid, d in rest.get('tables', {}).items():
                self.waypoints[f"table_{tid}"] = {
                    'x': float(d['x']),
                    'y': float(d['y']),
                    'theta': float(d.get('theta', 0.0))
                }
            self.get_logger().info(
                f"📍 {len(self.waypoints)} waypoints"
            )
        except Exception as e:
            self.get_logger().error(f"❌ {e}")
            self.waypoints = {
                'base':    {'x': 0.0,'y': 0.0,'theta': 0.0},
                'kitchen': {'x': 5.0,'y': 0.0,'theta': 1.57},
                'charging':{'x':-1.0,'y': 0.0,'theta': 0.0},
                'table_1': {'x': 2.0,'y': 1.0,'theta': 0.0},
                'table_2': {'x': 2.0,'y': 3.0,'theta': 0.0},
                'table_3': {'x': 4.0,'y': 1.0,'theta': 0.0},
                'table_4': {'x': 4.0,'y': 3.0,'theta': 0.0},
            }

    def _cb_goal(self, msg: String):
        target = msg.data.strip()
        if target not in self.waypoints:
            self.get_logger().error(f"❌ {target} не найден!")
            self._pub_status("FAILED", target)
            return
        with self._goal_lock:
            if self.goal_handle is not None:
                self._pending = target
                self.goal_handle.cancel_goal_async(
                ).add_done_callback(self._cb_cancel)
            else:
                self.current_target = target
                self._send_goal(target)

    def _send_goal(self, target: str):
        wp   = self.waypoints[target]
        pose = PoseStamped()
        pose.header.frame_id  = 'map'
        pose.header.stamp     = self.get_clock().now().to_msg()
        pose.pose.position.x  = wp['x']
        pose.pose.position.y  = wp['y']
        pose.pose.position.z  = 0.0
        pose.pose.orientation = self._yaw(wp.get('theta',0.0))
        goal      = NavigateToPose.Goal()
        goal.pose = pose
        self.get_logger().info(f"🚶 → {target}")
        self._pub_status("STARTED", target)
        self._face("🚶")
        fut = self.nav_client.send_goal_async(
            goal, feedback_callback=self._cb_feedback
        )
        fut.add_done_callback(self._cb_response)

    def _cb_response(self, future):
        with self._goal_lock:
            self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.get_logger().error("❌ Goal отклонён!")
            self._pub_status("REJECTED", self.current_target or "")
            with self._goal_lock:
                self.goal_handle    = None
                self.current_target = None
            return
        self.goal_handle.get_result_async(
        ).add_done_callback(self._cb_result)

    def _cb_feedback(self, feedback_msg):
        pass

    def _cb_result(self, future):
        result = future.result()
        S = {4:"SUCCEEDED", 5:"CANCELED", 6:"ABORTED"}
        status = S.get(result.status, "UNKNOWN")
        target = self.current_target or ""
        self.get_logger().info(f"🏁 {status} → {target}")
        self._pub_status(status, target)
        if result.status == 4:
            self._on_arrival(target)
        with self._goal_lock:
            self.goal_handle    = None
            self.current_target = None
            pending = self._pending
            self._pending = None
        if pending:
            self.current_target = pending
            self._send_goal(pending)

    def _cb_cancel(self, future):
        with self._goal_lock:
            self.goal_handle = None
            pending = self._pending
            self._pending = None
        if pending:
            self.current_target = pending
            self._send_goal(pending)

    def _on_arrival(self, target: str):
        if target.startswith('table_'):
            tid = target.split('_')[1]
            self._speak(
                f"🍽️ Стол №{tid}! Приятного аппетита!"
            )
            self._face("🍽️")
            self._tray("OPEN")
        elif target == 'kitchen':
            self._speak("🍳 Я на кухне. Загрузите заказ.")
            self._face("🍳")
            self._tray("LOAD")
        elif target == 'base':
            self._speak("🏠 Я на базе. Готов!")
            self._face("😊")
        elif target == 'charging':
            self._speak("🔋 Начинаю зарядку.")
            self._face("🔋")

    def _pub_status(self, status: str, target: str):
        msg = String()
        msg.data = json.dumps(
            {"status": status, "target": target}
        )
        self.pub_status.publish(msg)

    def _speak(self, text: str):
        msg = String(); msg.data = text
        self.pub_speech.publish(msg)

    def _face(self, emoji: str):
        msg = String(); msg.data = emoji
        self.pub_face.publish(msg)

    def _tray(self, cmd: str):
        msg = String(); msg.data = cmd
        self.pub_tray.publish(msg)

    @staticmethod
    def _yaw(yaw: float) -> Quaternion:
        q = Quaternion()
        q.z = math.sin(yaw / 2.0)
        q.w = math.cos(yaw / 2.0)
        return q


def main():
    rclpy.init()
    node = Nav2ClientNode()
    executor = rclpy.executors.MultiThreadedExecutor()
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
