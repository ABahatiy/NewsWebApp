# handlers_misc.py

import logging
from telebot.types import Message

from bot_instance import bot
from storage import storage
from keyboards import main_menu_kb, settings_kb, keywords_kb, topics_kb
from handlers_news import handle_news_command
from llm_agent import chat_with_llm
from config import USE_LLM, topics_text, get_topic_by_key
from utils_text import split_for_telegram

logger = logging.getLogger(__name__)


def _parse_list(text: str):
    text = (text or "").strip()
    text = text.replace(";", ",")
    return [x.strip().lower() for x in text.split(",") if x.strip()]


def handle_text(message: Message) -> None:
    chat_id = message.chat.id
    text = (message.text or "").strip()
    if not text:
        return

    storage.add_user_if_not_exists(chat_id)

    # Команди як резерв (щоб не було "не знаю що робити")
    if text.startswith("/"):
        cmd = text.split()[0].lower()
        if cmd in ("/start",):
            bot.send_message(chat_id, "Головне меню:", reply_markup=main_menu_kb())
            return
        if cmd in ("/news",):
            handle_news_command(message)
            return
        if cmd in ("/help",):
            bot.send_message(chat_id, "Керування через кнопки: Останні новини / Теми / Ключові слова / Налаштування.")
            return

        bot.send_message(chat_id, "Використайте кнопки меню.", reply_markup=main_menu_kb())
        return

    state = storage.get_input_state(chat_id)

    # --------- СТАНИ ВВОДУ ----------
    if state == "await_keywords":
        keywords = _parse_list(text)
        storage.set_keywords(chat_id, keywords)
        storage.set_input_state(chat_id, "")
        bot.send_message(chat_id, f"Ключові слова збережено: {', '.join(keywords) if keywords else '(порожньо)'}", reply_markup=main_menu_kb())
        return

    if state == "await_topics":
        raw = text.strip().lower()
        if raw == "all":
            storage.clear_topics(chat_id)  # порожньо = всі
            storage.set_input_state(chat_id, "")
            bot.send_message(chat_id, "Теми очищено: тепер новини надходитимуть з усіх тем.", reply_markup=main_menu_kb())
            return

        topics = _parse_list(text)
        # Валідація: залишаємо тільки ті ключі, що існують у TOPICS
        valid = []
        for t in topics:
            if get_topic_by_key(t):
                valid.append(t)

        storage.set_topics(chat_id, valid)
        storage.set_input_state(chat_id, "")
        bot.send_message(chat_id, f"Теми збережено: {', '.join(valid) if valid else '(не вибрано, буде всі теми)'}", reply_markup=main_menu_kb())
        return

    if state == "await_interval":
        try:
            minutes = int(text)
            storage.set_auto_interval(chat_id, minutes * 60)
            storage.set_input_state(chat_id, "")
            bot.send_message(chat_id, f"Інтервал автонадсилання: {minutes} хв.", reply_markup=main_menu_kb())
        except Exception:
            bot.send_message(chat_id, "Введіть число — інтервал у хвилинах (наприклад: 30).")
        return

    # --------- КНОПКИ МЕНЮ ----------
    t = text.strip().lower()

    if t in {"останні новини", "новини", "news"}:
        handle_news_command(message)
        return

    if t == "налаштування":
        bot.send_message(chat_id, "Налаштування:", reply_markup=settings_kb())
        return

    if t == "ключові слова":
        bot.send_message(chat_id, "Ключові слова:", reply_markup=keywords_kb())
        return

    if t == "задати ключові слова":
        storage.set_input_state(chat_id, "await_keywords")
        bot.send_message(chat_id, "Введіть ключові слова через кому (наприклад: спорт, україна, технології):")
        return

    if t == "очистити ключові слова":
        storage.clear_keywords(chat_id)
        bot.send_message(chat_id, "Ключові слова очищено. Тепер новини надходитимуть без фільтрації.", reply_markup=main_menu_kb())
        return

    if t == "теми":
        bot.send_message(chat_id, topics_text(), reply_markup=topics_kb())
        return

    if t == "задати теми":
        storage.set_input_state(chat_id, "await_topics")
        bot.send_message(chat_id, topics_text())
        return

    if t == "очистити теми":
        storage.clear_topics(chat_id)
        bot.send_message(chat_id, "Теми очищено: тепер новини надходитимуть з усіх тем.", reply_markup=main_menu_kb())
        return

    if t == "інтервал автонадсилання":
        storage.set_input_state(chat_id, "await_interval")
        bot.send_message(chat_id, "Введіть інтервал у хвилинах (наприклад: 30):")
        return

    if t == "допомога":
        bot.send_message(
            chat_id,
            "Як користуватись:\n"
            "1) 'Теми' — оберіть теми (або очистіть, щоб були всі).\n"
            "2) 'Ключові слова' — задайте фільтр за словами (або очистіть).\n"
            "3) 'Останні новини' — отримаєте дайджест.\n"
            "4) Будь-який інший текст — це чат з агентом.",
            reply_markup=main_menu_kb(),
        )
        return

    if t == "назад":
        bot.send_message(chat_id, "Головне меню:", reply_markup=main_menu_kb())
        return

    # --------- ЧАТ З АГЕНТОМ (за замовчуванням) ----------
    if USE_LLM:
        try:
            storage.add_chat_message(chat_id, "user", text)
            history = storage.get_chat_history(chat_id)
            reply = chat_with_llm(history, text)
            storage.add_chat_message(chat_id, "assistant", reply)

            for part in split_for_telegram(reply):
                bot.send_message(chat_id, part, disable_web_page_preview=True)
        except Exception as exc:
            logger.exception("Помилка чату з LLM: %s", exc)
            bot.send_message(chat_id, "Не вдалося отримати відповідь від ШІ. Спробуйте пізніше.")
        return

    bot.send_message(chat_id, "Спробуйте кнопки меню.", reply_markup=main_menu_kb())
