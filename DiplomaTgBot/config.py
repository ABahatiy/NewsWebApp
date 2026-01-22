import os
import logging
from urllib.parse import quote

# --- Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# --- DB ---
DB_PATH = os.getenv("DB_PATH", "bot_data.sqlite3")

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def setup_logging() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

# --- News fetch ---
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 8))
MAX_ITEMS_TOTAL = int(os.getenv("MAX_ITEMS_TOTAL", 60))
MAX_FETCH_DURATION_SEC = float(os.getenv("MAX_FETCH_DURATION_SEC", 20))

# --- Auto sender ---
AUTO_NEWS_INTERVAL_SEC = int(os.getenv("AUTO_NEWS_INTERVAL_SEC", 1800))

# --- Digest ---
DIGEST_ITEMS_LIMIT = int(os.getenv("DIGEST_ITEMS_LIMIT", 6))
DIGEST_MAX_CHARS = int(os.getenv("DIGEST_MAX_CHARS", 3500))

# --- LLM ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SEC = float(os.getenv("OPENAI_TIMEOUT_SEC", 25))
LLM_MAX_INPUT_CHARS = int(os.getenv("LLM_MAX_INPUT_CHARS", 3500))
USE_LLM = os.getenv("USE_LLM", "1") == "1"
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", 20))

# --- CORS ---
# приклад: "https://newswebapp-pied.vercel.app,http://localhost:3000"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").strip()

# --- Topics (фіксовані, для меню) ---
# key — те, що зберігаємо в БД
TOPICS = [
    {"key": "ukraine", "label": "Україна", "query": "Україна"},
    {"key": "world", "label": "Світ", "query": "Світ"},
    {"key": "politics", "label": "Політика", "query": "Політика"},
    {"key": "economy", "label": "Економіка", "query": "Економіка"},
    {"key": "technology", "label": "Технології", "query": "Технології"},
    {"key": "science", "label": "Наука", "query": "Наука"},
    {"key": "sport", "label": "Спорт", "query": "Спорт"},
    {"key": "business", "label": "Бізнес", "query": "Бізнес"},
    {"key": "health", "label": "Здоров’я", "query": "Здоров’я"},
    {"key": "cinema", "label": "Кіно", "query": "Кіно"},
    {"key": "games", "label": "Ігри", "query": "Ігри"},
]

def get_topic_by_key(key: str):
    key = (key or "").strip().lower()
    for t in TOPICS:
        if t["key"] == key:
            return t
    return None

def topics_text() -> str:
    lines = ["Доступні теми:"]
    for i, t in enumerate(TOPICS, start=1):
        lines.append(f"{i}) {t['label']} (ключ: {t['key']})")
    lines.append("")
    lines.append("Введіть ключі тем через кому (наприклад: sport, technology)")
    lines.append("Або напишіть: all — щоб обрати всі теми")
    return "\n".join(lines)

# --- Sources (Google News RSS) ---
def _google_news_rss_url(query: str, lang: str = "uk", region: str = "UA") -> str:
    q = quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={region}&ceid={region}:{lang}"

NEWS_SOURCES = [
    {
        "type": "google_news_rss",
        "key": t["key"],
        "topic": t["label"],
        "query": t["query"],
        "url": _google_news_rss_url(t["query"]),
    }
    for t in TOPICS
]

# --- Backward-compatible alias ---
# Старий код/імпорти можуть очікувати RSS_URLS
RSS_URLS = [s["url"] for s in NEWS_SOURCES]
