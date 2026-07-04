#!/usr/bin/env python3
"""
🔊 TTS NODE v3.1 — SmartWaiter
Голос робота (Piper TTS) — 4 языка
Топики: /robot/speech → /tts_status
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import re, subprocess, os, tempfile
import threading, queue
from pathlib import Path


class TTSNode(Node):

    def __init__(self):
        super().__init__('tts_node')
        self.get_logger().info("🔊 TTS Node v3.1 запускается...")

        self.declare_parameter('models_dir',   'models/tts')
        self.declare_parameter('play_command', 'aplay')

        self.models_dir = self.get_parameter('models_dir').value
        self.play_cmd   = self.get_parameter('play_command').value

        self.models = {
            'ru': f"{self.models_dir}/ru_RU-irina-medium.onnx",
            'tj': f"{self.models_dir}/ru_RU-irina-medium.onnx",
            'en': f"{self.models_dir}/en_US-lessac-medium.onnx",
            'zh': f"{self.models_dir}/zh_CN-huayan-medium.onnx",
        }
        self._check_models()

        self.queue = queue.PriorityQueue(maxsize=10)
        self.pub_status = self.create_publisher(
            String, '/tts_status', 10
        )
        self.create_subscription(
            String, '/robot/speech', self._cb_speech, 10
        )
        threading.Thread(
            target=self._worker, daemon=True
        ).start()

        self.get_logger().info("✅ TTS Node готов!")

    def _check_models(self):
        Path(self.models_dir).mkdir(parents=True, exist_ok=True)
        for lang, path in self.models.items():
            if not os.path.exists(path):
                self.get_logger().warn(f"⚠️ Модель не найдена: {path}")

    def _cb_speech(self, msg: String):
        text = msg.data.strip()
        if not text:
            return
        text_clean = re.sub(
            r'[^\w\s\-.,!?а-яА-ЯёЁa-zA-Z0-9\u4e00-\u9fff]',
            '', text
        ).strip()
        if not text_clean:
            return
        lang     = self._detect(text_clean)
        priority = 0 if any(
            w in text_clean.lower()
            for w in ['внимание', 'стоп', 'диккат']
        ) else 5
        try:
            self.queue.put_nowait((priority, text_clean, lang))
        except queue.Full:
            self.get_logger().warn("⚠️ TTS очередь полная")

    def _detect(self, text: str) -> str:
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            return 'zh'
        tajik = {'салом','хуш','ташаккур','лутфан','хайр','ман','мо'}
        if set(text.lower().split()) & tajik:
            return 'tj'
        first = text.strip().split()[0] if text.strip() else ''
        if first and all(ord(c) < 128 for c in first):
            return 'en'
        return 'ru'

    def _worker(self):
        while rclpy.ok():
            try:
                priority, text, lang = self.queue.get(timeout=0.5)
                self._speak(text, lang)
            except queue.Empty:
                continue

    def _speak(self, text: str, lang: str):
        model = self.models.get(lang, self.models['ru'])
        if not os.path.exists(model):
            self.get_logger().error(f"❌ Модель не найдена: {model}")
            return
        self._pub_status("SPEAKING", text[:50])
        with tempfile.NamedTemporaryFile(
            suffix='.wav', delete=False
        ) as tmp:
            wav = tmp.name
        try:
            res = subprocess.run(
                ['piper', '--model', model,
                 '--output_file', wav, '--text', text],
                capture_output=True, text=True, timeout=30
            )
            if res.returncode != 0:
                self.get_logger().error(f"❌ Piper: {res.stderr}")
                return
            for player in [self.play_cmd, 'paplay', 'aplay']:
                pr = subprocess.run(
                    [player, wav],
                    capture_output=True, timeout=60
                )
                if pr.returncode == 0:
                    break
            self.get_logger().info(f"🔊 [{lang}]: {text[:50]}")
            self._pub_status("IDLE", "")
        except Exception as e:
            self.get_logger().error(f"❌ TTS: {e}")
            self._pub_status("ERROR", str(e)[:50])
        finally:
            try:
                os.unlink(wav)
            except OSError:
                pass

    def _pub_status(self, status: str, info: str):
        msg = String()
        msg.data = f"{status}|{info}"
        self.pub_status.publish(msg)


def main():
    rclpy.init()
    node = TTSNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
