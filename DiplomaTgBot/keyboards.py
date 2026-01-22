# keyboards.py

from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("Останні новини"), KeyboardButton("Теми"))
    kb.row(KeyboardButton("Ключові слова"), KeyboardButton("Налаштування"))
    kb.row(KeyboardButton("Допомога"))
    return kb


def settings_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("Інтервал автонадсилання"))
    kb.row(KeyboardButton("Назад"))
    return kb


def keywords_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("Задати ключові слова"), KeyboardButton("Очистити ключові слова"))
    kb.row(KeyboardButton("Назад"))
    return kb


def topics_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("Задати теми"), KeyboardButton("Очистити теми"))
    kb.row(KeyboardButton("Назад"))
    return kb
