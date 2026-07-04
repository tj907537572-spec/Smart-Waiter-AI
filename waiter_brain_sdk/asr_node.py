#!/usr/bin/env python3
"""
🎤 ASR NODE v3.1 — SmartWaiter
Слух робота (Whisper) — 4 языка
Топики: микрофон → /voice_command
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import numpy as np
import threading
import time
import os
import wave
import tempfile
from collections import deque


class ASRNode(Node):

    def __init__(self):
        super().__init__('asr_node')
        self.get_logger().info("🎤 ASR Node v3.1 запускается...")

        self.declare_parameter('model_size',        'base')
        self.declare_parameter('sample_rate',       16000)
        self.declare_parameter('silence_threshold', 500)
        self.declare_parameter('silence_duration',  1.5)

        self.model_size    = self.get_parameter('model_size').value
        self.sample_rate   = self.get_parameter('sample_rate').value
        self.sil_threshold = self.get_parameter('silence_threshold').value
        self.sil_duration  = self.get_parameter('silence_duration').value

        self.model      = None
        self.use_faster = False
        self._load_model()

        self.pub_voice  = self.create_publisher(
            String, '/voice_command', 10
        )
        self.pub_status = self.create_publisher(
            String, '/asr_status', 10
        )

        self.audio_buffer   = deque(maxlen=int(self.sample_rate * 10))
        self.is_recording   = False
        self.silence_start  = 0.0
        self._has_new_audio = False

        threading.Thread(
            target=self._record_loop, daemon=True
        ).start()

        self.create_timer(0.5, self._process_timer)
        self.get_logger().info("✅ ASR Node готов!")
        self._pub_status("LISTENING")

    def _load_model(self):
        self.get_logger().info(
            f"⏳ Загрузка Whisper '{self.model_size}'..."
        )
        try:
            from faster_whisper import WhisperModel
            self.model      = WhisperModel(
                self.model_size, device="cpu", compute_type="int8"
            )
            self.use_faster = True
            self.get_logger().info("✅ Faster-Whisper загружен")
        except ImportError:
            try:
                import whisper
                self.model      = whisper.load_model(self.model_size)
                self.use_faster = False
                self.get_logger().info("✅ Whisper загружен")
            except Exception as e:
                self.get_logger().error(f"❌ Whisper не найден: {e}")

    def _record_loop(self):
        try:
            import pyaudio
        except ImportError:
            self.get_logger().error("❌ pyaudio не найден")
            return
        pa     = pyaudio.PyAudio()
        stream = None
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            self.get_logger().info("🎙️ Микрофон активирован")
            while rclpy.ok():
                try:
                    data  = stream.read(
                        1024, exception_on_overflow=False
                    )
                    chunk = np.frombuffer(data, dtype=np.int16)
                    vol   = float(np.abs(chunk).mean())
                    if vol > self.sil_threshold:
                        if not self.is_recording:
                            self.is_recording  = True
                            self.audio_buffer.clear()
                            self.silence_start = 0.0
                            self._pub_status("RECORDING")
                        self.audio_buffer.extend(chunk)
                    elif self.is_recording:
                        self.audio_buffer.extend(chunk)
                        now = time.time()
                        if self.silence_start == 0.0:
                            self.silence_start = now
                        elif now - self.silence_start >= self.sil_duration:
                            self.is_recording   = False
                            self.silence_start  = 0.0
                            self._has_new_audio = True
                            self._pub_status("PROCESSING")
                except Exception as e:
                    time.sleep(0.05)
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            pa.terminate()

    def _process_timer(self):
        if not self._has_new_audio or self.model is None:
            return
        self._has_new_audio = False
        if len(self.audio_buffer) < self.sample_rate * 0.5:
            self._pub_status("LISTENING")
            return
        audio_np = np.array(
            self.audio_buffer, dtype=np.float32
        ) / 32768.0
        self.audio_buffer.clear()
        with tempfile.NamedTemporaryFile(
            suffix='.wav', delete=False
        ) as tmp:
            wav_path = tmp.name
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(
                    (audio_np * 32768.0).astype(
                        np.int16
                    ).tobytes()
                )
            self.get_logger().info("🧠 Распознаю речь...")
            text, lang = self._transcribe(wav_path)
            if text:
                self.get_logger().info(
                    f"🎤 [{lang}]: {text}"
                )
                msg      = String()
                msg.data = text
                self.pub_voice.publish(msg)
                self._pub_status(f"RECOGNIZED|{lang}")
            else:
                self._pub_status("LISTENING")
        except Exception as e:
            self.get_logger().error(f"❌ ASR: {e}")
            self._pub_status("ERROR")
        finally:
            try:
                os.unlink(wav_path)
            except OSError:
                pass

    def _transcribe(self, wav_path: str):
        if self.use_faster:
            segments, info = self.model.transcribe(
                wav_path, beam_size=5
            )
            text = " ".join(s.text for s in segments).strip()
            return text, info.language
        else:
            result = self.model.transcribe(
                wav_path, fp16=False
            )
            return result["text"].strip(), result.get("language", "ru")

    def _pub_status(self, status: str):
        msg      = String()
        msg.data = status
        self.pub_status.publish(msg)


def main():
    rclpy.init()
    node = ASRNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
