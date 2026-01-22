# auto_sender.py

import threading
import time
import logging

from bot_instance import bot
from storage import storage
from news_fetcher import fetch_news
from config import AUTO_NEWS_INTERVAL_SEC, USE_LLM, DIGEST_ITEMS_LIMIT
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
            lines.append(f"• <b>{topic}</b>\n{title}\n{html_link('Детальніше', link)}")
        else:
            lines.append(f"• {title}\n{html_link('Детальніше', link)}")

    return "<b>Оновлення новин</b>\n\n" + "\n\n".join(lines)


class AutoNewsSender(threading.Thread):
    def __init__(self, interval_sec: int) -> None:
        super().__init__(name="auto-news-sender", daemon=True)
        self.interval_sec = max(60, interval_sec)
        self._stop_flag = False

    def stop(self) -> None:
        self._stop_flag = True

    def run(self) -> None:
        logger.info("Фоновий агент автонадсилання новин запущений з інтервалом %s сек.", self.interval_sec)
        while not self._stop_flag:
            try:
                self._run_cycle()
            except Exception as exc:
                logger.exception("Помилка в автонадсиланні новин: %s", exc)
            time.sleep(self.interval_sec)

    def _run_cycle(self) -> None:
        chat_ids = storage.get_all_chat_ids()
        if not chat_ids:
            return

        logger.info("Запуск автооновлення новин для %d користувачів", len(chat_ids))

        for chat_id in chat_ids:
            keywords = storage.get_keywords(chat_id)
            ignore_keywords = not bool(keywords)

            items = fetch_news(
                keywords=keywords,
                limit_per_feed=8,
                ignore_keywords=ignore_keywords,
            )

            if not items:
                continue

            new_items = storage.filter_new_items(chat_id, items)
            if not new_items:
                continue

            candidates = new_items[: max(12, DIGEST_ITEMS_LIMIT * 3)]

            if USE_LLM:
                try:
                    chosen = select_relevant_items_with_llm(candidates, keywords, max_keep=DIGEST_ITEMS_LIMIT)
                    digest_text = build_digest_with_llm(chosen, keywords)

                    storage.add_chat_message(chat_id, "assistant", digest_text)

                    for part in split_for_telegram(digest_text):
                        bot.send_message(chat_id, part, disable_web_page_preview=True)
                    continue

                except Exception as exc:
                    logger.warning("LLM-дайджест не вдався, fallback: %s", exc)

            # fallback HTML
            fallback_items = candidates[:DIGEST_ITEMS_LIMIT]
            digest_html = _build_fallback_digest_html(fallback_items)

            storage.add_chat_message(chat_id, "assistant", digest_html)

            for part in split_for_telegram(digest_html):
                bot.send_message(chat_id, part, parse_mode="HTML", disable_web_page_preview=True)


def start_auto_sender() -> AutoNewsSender:
    sender = AutoNewsSender(AUTO_NEWS_INTERVAL_SEC)
    sender.start()
    return sender
