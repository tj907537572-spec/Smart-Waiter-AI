# PROFESSIONAL UNIVERSAL AI EVENT & RESTAURANT CORE
# Focus: Guest Engagement, Hospitality, Humor, and Multi-Language Entertainment
# Modes: "restaurant" (Кафе/Ресторан), "wedding" (Свадьбы/Торжества)

import random

class SmartRobotBrain:
    def __init__(self):
        # 1. Системные настройки
        self.safety_dist = 0.7       
        self.current_lang = "tj"     
        self.current_mode = "restaurant" 
        self.system_status = "OK"    
        
        # 2. БАЗА ДЛЯ РЕЖИМА "РЕСТОРАН" (Привлечение гостей, комплименты, юмор)
        self.restaurant_entertainment = {
            "приветствие": {
                "tj": "Ассалому алейкум! Хуш омадед ба макони хуштамъ ва заковат! Шумо имрӯз хеле зебоед!",
                "ru": "Добро пожаловать в обитель вкуса и уюта! Вы сегодня просто потрясающе выглядите!",
                "en": "Welcome to our restaurant! You look absolutely wonderful today!",
                "zh": "欢迎光临我们的餐厅！您今天看起来真是太美.了！"
            },
            "шутка": {
                "tj": "Медонед чаро ман беҳтарин пешхизматам? Чунки ман ҳеҷ гоҳ аз таоми шумо намехӯрам ва чойпулӣ намепурсам!",
                "ru": "Знаете, почему я идеальный официант? Я никогда не съем вашу картошку фри и не прошу чаевых!",
                "en": "Do you know why I am the perfect waiter? I never eat your fries and I don't ask for tips!",
                "zh": "你知道为什么我是完美的男服务员吗？我从不偷吃你的薯条，也不要小费！"
            },
            "комплимент": {
                "tj": "Интихоби шумо супер аст! Ин ҷо беҳтарин инсонҳо ҷамъ шудаанд. Аз лаҳзаҳо лаззат баред!",
                "ru": "Ваш выбор безупречен! В этом заведении собираются только самые лучшие люди. Приятного отдыха!",
                "en": "Your choice is perfect! Only the best people gather here. Have a wonderful time!",
                "zh": "您的选择太棒了！只有最优秀的人才会聚集在这里。祝您度过美好时光！"
            }
        }

        # 3. БАЗА ДЛЯ РЕЖИМА "СВАДЬБА / ТУЙ" (Тосты, интерактив, поздравления)
        self.wedding_entertainment = {
            "поздравление": {
                "tj": "Ҷавонони азиз, хонаводаи навбанёд муборак бошад! Илоҳо хушбахту хонаобод шавед, сад сола шавед!",
                "ru": "Дорогие молодожены! Пусть ваша совместная жизнь будет сладкой, как свадебный торт! Горько!",
                "en": "Dear newlyweds, congratulations! Wishing you endless love, joy, and a beautiful life together!",
                "zh": "恭喜新婚快乐！祝你们相亲相爱，白头偕老，幸福美满！"
            },
            "шутка": {
                "tj": "Меҳмонони азиз, камтар рақс кунед, варақсанд! Саломатии домоду арӯсро фаромӯш накунед!",
                "ru": "Дорогие гости, не стесняйтесь! Танцуйте так, будто вас никто не снимает на телефон!",
                "en": "Dear guests, don't be shy! Dance like nobody is recording you on their phones!",
                "zh": "尊贵的来宾们，别害羞！尽情跳舞吧，就像没有人用手机拍 group 一样！"
            },
            "чай": {
                "tj": "Марҳамат, чойи гарми тоҷикиро гиред. Саломат бошед!",
                "ru": "Пожалуйста, угощайтесь горячим праздничным чаем. Ваше здоровье!",
                "en": "Please, have some hot traditional tea. To your health!",
                "zh": "请享用热腾腾的传统茶。祝 planetary 健康！"
            }
        }

    def set_mode(self, mode_name):
        if mode_name in ["restaurant", "wedding"]:
            self.current_mode = mode_name
            return f"SYSTEM: Mode changed to {mode_name.upper()}"
        return "SYSTEM ERROR: Unknown mode"

    def set_language(self, lang_code):
        self.current_lang = lang_code if lang_code in ["tj", "ru", "en", "zh"] else "tj"
        return f"Language set to {self.current_lang.upper()}"

    # --- УНИВЕРСАЛЬНЫЙ СЦЕНАРИЙ ОБЩЕНИЯ И РАЗНОСА ---
    def handle_interaction(self, input_command):
        command = input_command.lower()
        current_lang = self.current_lang

        # 1. РЕЖИМ РЕСТОРАНА (Шоу и привлечение)
        if self.current_mode == "restaurant":
            if command in self.restaurant_entertainment:
                speech = self.restaurant_entertainment[command][current_lang]
                return f"[ДВИЖЕНИЕ]: Робот плавно подходит к гостям и включает анимацию лица.\n🤖 РОБОТ ГОВОРИТ: {speech}"
            
            # Если команда свободная (например, просто погладили или нажали экран)
            default_responses = {
                "tj": "Ман барои хизмати шумо ҳамеша омодаам! Бо ман сурат гиред ва ба дӯстонатон нишон диҳед!",
                "ru": "Я всегда рад дарить вам улыбки! Сделайте со мной фото и покажите друзьям!",
                "en": "I'm always happy to bring you joy! Take a photo with me and share it!"
            }
            return f"[ДВИЖЕНИЕ]: Робот мигает диодами.\n🤖 РОБОТ: {default_responses.get(current_lang, default_responses['tj'])}"

        # 2. РЕЖИМ СВАДЬБЫ
        elif self.current_mode == "wedding":
            if command in self.wedding_entertainment:
                speech = self.wedding_entertainment[command][current_lang]
                return f"[ДВИЖЕНИЕ]: Робот перемещается в праздничную зону зала.\n🎉 РОБОТ ГОВОРИТ: {speech}"
            
            default_wedding = {
                "tj": "Хуш омадед ба тӯйи бошукӯҳ! Имрӯз беҳтарин рӯз аст!",
                "ru": "Добро пожаловать на великолепное торжество! Пусть этот день запомнится навсегда!",
                "en": "Welcome to this grand celebration! Let's make it unforgettable!"
            }
            return f"🎉 РОБОТ: {default_wedding.get(current_lang, default_wedding['tj'])}"

    # --- СИСТЕМА БЕЗОПАСНОСТИ ДВИЖЕНИЯ С ПОДНОСАМИ ---
    def check_navigation(self, distance_to_human):
        if distance_to_human <= 0.3: 
            self.system_status = "EMERGENCY"
            return "ALARM: Экстренный стоп! Защита гостей и подносов от столкновения!"
            
        if distance_to_human < self.safety_dist:
            requests = {
                "tj": "Бубахшед, илтимос ба ман масир диҳед, ман барои шумо шодӣ мебарам.",
                "ru": "Простите, пожалуйста, разрешите пройти. Я везу вам хорошее настроение!",
                "en": "Excuse me, please let me pass, I'm bringing joy to your table!",
                "zh": "不好意思，请让我过一下。"
            }
            return f"🤖 РОБОТ ПРОСИТ: {requests.get(self.current_lang, requests['tj'])}"
            
        return "STATUS: Путь свободен. Робот продолжает радовать гостей."
