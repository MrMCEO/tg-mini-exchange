import os
import json
import telebot
from telebot.types import WebAppInfo, MenuButtonWebApp, InlineKeyboardMarkup, InlineKeyboardButton
from logger import Logger

# Создание логгера
logger = Logger()

# Загрузка конфигурации
def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        error_msg = "Ошибка: файл config.json не найден"
        logger.log_error("config_loading", error_msg)
        print(error_msg)
        exit(1)

config = load_config()

# Инициализация бота
bot = telebot.TeleBot(config['BOT_TOKEN'])

@bot.message_handler(commands=['start'])
def start(message):
    try:
        # Перезагружаем конфигурацию для получения актуального URL
        current_config = load_config()
        
        # Создаем клавиатуру с кнопкой для запуска веб-приложения
        markup = InlineKeyboardMarkup()
        webapp_button = InlineKeyboardButton(
            text="Открыть биржу", 
            web_app=WebAppInfo(url=current_config['WEBAPP_URL'])
        )
        markup.add(webapp_button)
        
        # Отправляем приветственное сообщение с кнопкой
        bot.send_message(
            message.chat.id,
            "Добро пожаловать в Учебную Биржу! 📊\n\n"
            "Нажмите кнопку ниже, чтобы начать торговлю:",
            reply_markup=markup
        )

        # Устанавливаем кнопку меню
        menu_button = MenuButtonWebApp(
            type="web_app",
            text="Биржа",
            web_app=WebAppInfo(url=current_config['WEBAPP_URL'])
        )
        bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=menu_button
        )
        
        # Логируем действие пользователя
        logger.log_user_action(
            message.chat.id, 
            "bot_start", 
            {"username": message.from_user.username}
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.log_error(
            "bot_start", 
            error_msg,
            {"user_id": message.chat.id}
        )
        bot.reply_to(message, "Произошла ошибка при запуске бота. Попробуйте позже.")

@bot.message_handler(func=lambda message: True)
def echo(message):
    logger.log_user_action(
        message.chat.id,
        "message_received",
        {
            "text": message.text,
            "username": message.from_user.username
        }
    )
    bot.reply_to(message, "Используйте кнопку 'Биржа' для доступа к торговле")

if __name__ == "__main__":
    if not config['BOT_TOKEN']:
        error_msg = "Ошибка: Заполните BOT_TOKEN в файле config.json"
        logger.log_error("config_validation", error_msg)
        print(error_msg)
        exit(1)
    
    logger.log_user_action("system", "bot_started", {"token": config['BOT_TOKEN']})
    print("Бот запущен")
    bot.polling()
