import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import os
from ament_index_python.packages import get_package_share_directory

class UniversalWaiterBrain(Node):
    def __init__(self):
        super().__init__('waiter_brain_node')

        # 1. Параметры: регион и дистанция безопасности
        self.declare_parameter('region', 'tj')
        self.declare_parameter('safety_dist', 0.7)
        
        region = self.get_parameter('region').get_parameter_value().string_value
        self.safety_dist = self.get_parameter('safety_dist').get_parameter_value().double_value

        # 2. Загружаем культурный пак (меню и фразы) из JSON
        self.load_cultural_pack(region)

        # 3. Состояние робота
        self.state = "waiting_order"
        self.last_dish = None
        self.current_lang = self.pack.get("default_lang", "tj")

        # 4. ROS 2 Издатели и Подписчики
        # Слушаем заказы и команды смены языка
        self.order_sub = self.create_subscription(String, '/order', self.order_callback, 10)
        self.lang_sub = self.create_subscription(String, '/set_language', self.lang_callback, 10)
        
        # Отправляем голос и команды навигации
        self.speak_pub = self.create_publisher(String, '/speak', 10)
        self.nav_pub = self.create_publisher(String, '/navigation_goal', 10)

        self.get_logger().info(f'--- WAITER BRAIN ACTIVE (Region: {region}) ---')
        self.speak("ROBOT: Система запущена. Я готов принимать заказы.")

    def load_cultural_pack(self, region):
        """Загрузка конфигурации из папки config"""
        try:
            package_share_directory = get_package_share_directory('waiter_brain_sdk')
            config_path = os.path.join(package_share_directory, 'config', f'{region}.json')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.pack = json.load(f)
            self.get_logger().info(f"Успешно загружен конфиг: {region}.json")
        except Exception as e:
            self.get_logger().error(f"Ошибка загрузки конфига: {e}")
            # Резервный вариант, если файл не найден
            self.pack = {"phrases": {"not_found": {"en": "Menu error"}}, "menu_logic": {}}

    def speak(self, text):
        """Публикация текста для голосового модуля робота"""
        msg = String()
        msg.data = text
        self.speak_pub.publish(msg)
        self.get_logger().info(f'Голос: {text}')

    def order_callback(self, msg):
        """Логика обработки заказа и активных продаж (Upselling)"""
        user_input = msg.data.lower().strip()
        
        if self.state == "waiting_order":
            if user_input in self.pack["menu_logic"]:
                self.last_dish = user_input
                self.state = "waiting_upsell_confirm"
                
                # Получаем шаблон фразы и рекомендацию для текущего языка
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
                self.get_logger().info(f"Успешная продажа: {self.last_dish}")
            else:
                self.speak(self.pack["phrases"]["thanks"][self.current_lang])
            
            self.state = "waiting_order"
            self.last_dish = None

    def lang_callback(self, msg):
        """Смена языка на лету (например, отправить 'zh' для китайского)"""
        new_lang = msg.data.lower().strip()
        if new_lang in ["tj", "ru", "en", "zh"]:
            self.current_lang = new_lang
            self.speak(self.pack["phrases"]["lang_switched"][new_lang])
            self.get_logger().info(f"Язык переключен на: {new_lang}")

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
