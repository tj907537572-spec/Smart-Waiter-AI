 import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os
from ament_index_python.packages import get_package_share_directory

class UniversalWaiterBrain(Node):
    def __init__(self):
        super().__init__('waiter_brain_node')

        # 1. Параметры
        self.declare_parameter('region', 'tj')
        region = self.get_parameter('region').get_parameter_value().string_value

        # 2. Загружаем конфиг
        self.load_cultural_pack(region)

        # 3. Состояние и языки
        self.state = "waiting_order"
        self.current_lang = self.pack.get("default_lang", "tj")
        self.supported_langs = ['tj', 'ru', 'en', 'zh']
        self.greeting_index = 0

        # 4. ROS 2 Издатели и Подписчики
        self.order_sub = self.create_subscription(String, '/order', self.order_callback, 10)
        self.lang_sub = self.create_subscription(String, '/set_language', self.lang_callback, 10)
        self.speak_pub = self.create_publisher(String, '/speak', 10)

        # 5. ТАЙМЕР ПРИВЕТСТВИЯ (Вариант №2)
        # Робот будет здороваться каждые 10 секунд, пока никто не сделал заказ
        self.greeting_timer = self.create_timer(10.0, self.cycle_greeting)

        self.get_logger().info('--- SMART WAITER ACTIVE: UNIVERSAL MODE ---')

    def load_cultural_pack(self, region):
        try:
            package_share_directory = get_package_share_directory('waiter_brain_sdk')
            config_path = os.path.join(package_share_directory, 'config', f'{region}.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.pack = json.load(f)
        except Exception as e:
            self.get_logger().error(f"Config error: {e}")
            self.pack = {"phrases": {"not_found": {"en": "Error"}}, "menu_logic": {}}

    def speak(self, text):
        msg = String()
        msg.data = text
        self.speak_pub.publish(msg)

    def cycle_greeting(self):
        """Робот по очереди здоровается, помогая клиенту выбрать язык"""
        if self.state == "waiting_order":
            lang = self.supported_langs[self.greeting_index]
            
            # Приветствия на разных языках
            greetings = {
                "tj": "Ассалому алейкум! Фармоиш медиҳед? Кнопкаро пахш кунед.",
                "ru": "Здравствуйте! Желаете сделать заказ? Нажмите кнопку на экране.",
                "en": "Hello! Would you like to order? Please touch the screen.",
                "zh": "你好！你想点菜吗？请碰屏幕。"
            }
            
            self.speak(greetings[lang])
            self.get_logger().info(f"Приветствие на языке: {lang}")
            
            # Переключаем индекс на следующий язык для следующего раза
            self.greeting_index = (self.greeting_index + 1) % len(self.supported_langs)

    def lang_callback(self, msg):
        """Когда клиент нажимает флаг на экране, робот переключается"""
        new_lang = msg.data.lower().strip()
        if new_lang in self.supported_langs:
            self.current_lang = new_lang
            # После выбора языка можно остановить таймер приветствий, если нужно
            # self.greeting_timer.cancel() 
            self.speak(self.pack["phrases"]["lang_switched"][new_lang])

    def order_callback(self, msg):
        """Логика заказа (плов -> салат)"""
        user_input = msg.data.lower().strip()
        # Если заказ начат, робот перестает здороваться на разных языках
        if user_input:
            self.process_logic(user_input)

    def process_logic(self, user_input):
        # Здесь остается твоя логика из предыдущего кода (upsell и т.д.)
        # ... (код обработки заказа) ...
        pass

def main(args=None):
    rclpy.init(args=args)
    node = UniversalWaiterBrain()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
