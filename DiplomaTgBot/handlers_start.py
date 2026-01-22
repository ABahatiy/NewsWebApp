# handlers_start.py

from telebot.types import Message

from bot_instance import bot
from storage import storage
from keyboards import main_menu_kb


def handle_start(message: Message) -> None:
    chat_id = message.chat.id
    storage.add_user_if_not_exists(chat_id)
    storage.set_input_state(chat_id, "")

    bot.send_message(
        chat_id,
        "Вітаю! Я бот моніторингу новин.\n"
        "Керування — через кнопки меню.",
        reply_markup=main_menu_kb(),
    )
