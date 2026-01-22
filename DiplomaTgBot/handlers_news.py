# handlers_news.py

import logging
from telebot.types import Message

from bot_instance import bot
from storage import storage
from news_fetcher import fetch_news
from config import USE_LLM, DIGEST_ITEMS_LIMIT
from utils_text import split_for_telegram, escape_html, html_link
from llm_agent import build_digest_with_llm, select_relevant_items_with_llm

logger = logging.getLogger(__name__)


def _build_fallback_digest_html(items):
    lines = []
    for it in items:
        title = escape_html(it.get("title", ""))
        topic = escape_html(it.get("topic", ""))
        link = it.get("link", "")

        if topic:
            lines.append(f"• <b>{topic}</b>: {title} — {html_link('Детальніше', link)}")
        else:
            lines.append(f"• {title} — {html_link('Детальніше', link)}")

    return "<b>Останні новини</b>\n\n" + "\n".join(lines)


def handle_news_command(message: Message) -> None:
    chat_id = message.chat.id
    storage.add_user_if_not_exists(chat_id)

    keywords = storage.get_keywords(chat_id)
    topics = storage.get_topics(chat_id)

    if keywords:
        bot.send_message(chat_id, f"Ключові слова: {', '.join(keywords)}")
    else:
        bot.send_message(chat_id, "Ключові слова не задані.")

    if topics:
        bot.send_message(chat_id, f"Теми: {', '.join(topics)}")
    else:
        bot.send_message(chat_id, "Теми не задані. Надсилаю новини з усіх тем.")

    items = fetch_news(
        keywords=keywords,
        limit_per_feed=6,
        ignore_keywords=not bool(keywords),
        selected_topics=topics if topics else None,
    )

    if not items:
        bot.send_message(chat_id, "Новин не знайдено (або джерела тимчасово недоступні).")
        return

    new_items = storage.filter_new_items(chat_id, items)
    if not new_items:
        bot.send_message(chat_id, "Немає нових новин (усі вже надсилались раніше).")
        return

    candidates = new_items[: max(12, DIGEST_ITEMS_LIMIT * 3)]

    if USE_LLM:
        try:
            chosen = select_relevant_items_with_llm(candidates, keywords, max_keep=DIGEST_ITEMS_LIMIT)
            digest_html = build_digest_with_llm(chosen, keywords)

            storage.add_chat_message(chat_id, "assistant", digest_html)

            for part in split_for_telegram(digest_html):
                bot.send_message(chat_id, part, parse_mode="HTML", disable_web_page_preview=True)
            return

        except Exception as exc:
            logger.warning("LLM-дайджест не спрацював, fallback: %s", exc)

    fallback_items = candidates[:DIGEST_ITEMS_LIMIT]
    digest_html = _build_fallback_digest_html(fallback_items)

    storage.add_chat_message(chat_id, "assistant", digest_html)

    for part in split_for_telegram(digest_html):
        bot.send_message(chat_id, part, parse_mode="HTML", disable_web_page_preview=True)
