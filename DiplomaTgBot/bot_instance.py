from telebot import TeleBot
from config import TELEGRAM_TOKEN

# Єдиний екземпляр бота, який імпортують усі хендлери
bot = TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
