# main.py

import logging
from dotenv import load_dotenv

load_dotenv()

from config import setup_logging, TELEGRAM_TOKEN
from bot_instance import bot
from auto_sender import start_auto_sender

from handlers_start import handle_start
from handlers_news import handle_news_command
from handlers_misc import handle_text

logger = logging.getLogger(__name__)


def register_handlers() -> None:
    bot.register_message_handler(handle_start, commands=["start"])
    bot.register_message_handler(handle_news_command, commands=["news"])

    bot.register_message_handler(handle_text, func=lambda m: True)


def main() -> None:
    setup_logging()

    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не заданий.")

    logger.info("Запуск бота…")

    register_handlers()
    start_auto_sender()

    logger.info("Бот запущений. Очікування повідомлень…")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)


if __name__ == "__main__":
    main()
