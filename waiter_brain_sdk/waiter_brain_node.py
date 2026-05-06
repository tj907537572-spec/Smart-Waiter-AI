 import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os
from ament_index_python.packages import get_package_share_directory

class UniversalWaiterBrain(Node):
    def __init__(self):
        super().__init__('waiter_brain_node')

        # 1. Параметры (регион по умолчанию - Таджикистан)
        self.declare_parameter('region', 'tj')
        region = self.get_parameter('region').get_parameter_value().string_value

        # 2. Загружаем культурный пак (фразы и меню)
        self.load_cultural_pack(region)

        # 3. Состояние робота и мультиязычность
        self.state = "waiting_order"
        self.current_lang = self.pack.get("default_lang", "tj")
        self.supported_langs = ['tj', 'ru', 'en', 'zh']
        self.greeting_index = 0
        self.last_dish = None

        # 4. ROS 2 Издатели и Подписчики
        self.order_sub = self.create_subscription(String, '/order', self.order_callback, 10)
        self.lang_sub = self.create_subscription(String, '/set_language', self.lang_callback, 10)
        self.speak_pub = self.create_publisher(String, '/speak', 10)

        # 5. ТАЙМЕР ПРИВЕТСТВИЯ (Вариант №2)
        # Каждые 10 секунд робот меняет язык приветствия, пока нет заказа
        self.greeting_timer = self.create_timer(10.0, self.cycle_greeting)

        self.get_logger().info(f'--- SMART WAITER AI ACTIVE (Region: {region}) ---')

    def load_cultural_pack(self, region):
        """Загрузка настроек из папки config"""
        try:
            package_share_directory = get_package_share_directory('waiter_brain_sdk')
            config_path = os.path.join(package_share_directory, 'config', f'{region}.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.pack = json.load(f)
        except Exception as e:
            self.get_logger().error(f"Ошибка конфига: {e}")
            self.pack = {"phrases": {"not_found": {"en": "Error"}}, "menu_logic": {}}

    def speak(self, text):
        """Отправка текста в голосовой модуль робота"""
        msg = String()
        msg.data = text
        self.speak_pub.publish(msg)

    def cycle_greeting(self):
        """Функция автономного приветствия на разных языках"""
        if self.state == "waiting_order":
            lang = self.supported_langs[self.greeting_index]
            
            greetings = {
                "tj": "Ассалому алейкум! Фармоиш медиҳед?",
                "ru": "Здравствуйте! Желаете что-нибудь заказать?",
                "en": "Hello! Would you like to order something?",
                "zh": "你好！你想点菜吗？"
            }
            
            self.speak(greetings[lang])
            self.get_logger().info(f"Здороваюсь на языке: {lang}")
            
            # Переход к следующему языку
            self.greeting_index = (self.greeting_index + 1) % len(self.supported_langs)

    def lang_callback(self, msg):
        """Смена языка, когда клиент нажал кнопку на экране"""
        new_lang = msg.data.lower().strip()
        if new_lang in self.supported_langs:
            self.current_lang = new_lang
            self.speak(self.pack["phrases"]["lang_switched"][new_lang])
            self.get_logger().info(f"Язык переключен на: {new_lang}")

    def order_callback(self, msg):
        """Логика обработки заказа и активных продаж"""
        user_input = msg.data.lower().strip()
        
        if self.state == "waiting_order":
            if user_input in self.pack["menu_logic"]:
                self.last_dish = user_input
                self.state = "waiting_upsell_confirm"
                
                # Берем шаблон фразы и рекомендацию
                template = self.pack["phrases"]["upsell"][self.current_lang]
                rec = self.pack["menu_logic"][user_input]["recommendation"][self.current_lang]
                
                response = template.format(dish=user_input, recommendation=rec)
                self.speak(response)
            else:
                self.speak(self.pack["phrases"]["not_found"][self.current_lang])

        elif self.state == "waiting_upsell_confirm":
            yes_words = self.pack["phrases"]["yes_words"][self.current_lang]
            if any(word in user_input for word in yes_words):
                self.speak(self.pack["phrases"]["upsell_ok"][self.current_lang])
            else:
                self.speak(self.pack["phrases"]["thanks"][self.current_lang])
            
            # Возвращаемся в режим ожидания нового гостя
            self.state = "waiting_order"
            self.last_dish = None

def main(args=None):
    rclpy.init(args=args)
    node = UniversalWaiterBrain()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

