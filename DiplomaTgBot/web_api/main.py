from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Твоя реальна функція збору новин
from news_fetcher import fetch_news  # <-- ОСЬ ВАЖЛИВИЙ РЯДОК

logger = logging.getLogger("web_api")

app = FastAPI(title="Diploma TgBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

setup_logging()

DEFAULT_TOPICS = [
    {"key": "all", "label": "Усі"},
    {"key": "ukraine", "label": "Україна"},
    {"key": "world", "label": "Світ"},
    {"key": "politics", "label": "Політика"},
    {"key": "economy", "label": "Економіка"},
    {"key": "technology", "label": "Технології"},
    {"key": "science", "label": "Наука"},
    {"key": "sport", "label": "Спорт"},
    {"key": "business", "label": "Бізнес"},
    {"key": "health", "label": "Здоров’я"},
    {"key": "cinema", "label": "Кіно"},
    {"key": "games", "label": "Ігри"},
]

@app.get("/health")
def health():
    return {
        "status": "ok",
        "news_fn_found": True,
        "news_fn_import": "news_fetcher.fetch_news",
    }

@app.get("/topics")
def topics():
    return {"topics": DEFAULT_TOPICS}

@app.get("/news")
def news(
    topic: str = Query(default="all"),
    q: str = Query(default=""),
    limit: int = Query(default=30, ge=1, le=100),
):
    """
    Повертаємо новини у форматі, зручному для веба.
    """
    keywords = [q] if q.strip() else []

    selected_topics: Optional[List[str]] = None
    if topic and topic != "all":
        selected_topics = [topic]

    # Виклик твоєї функції. Якщо сигнатура інша — скажеш, я піджену.
    items = fetch_news(
        keywords=keywords,
        selected_topics=selected_topics,
        limit_per_feed=6,
        ignore_keywords=False,
    )

    normalized: List[Dict[str, Any]] = []
    for i, it in enumerate((items or [])[:limit]):
        if not isinstance(it, dict):
            continue

        title = str(it.get("title", "")).strip()
        link = str(it.get("link", "")).strip()
        if not title or not link:
            continue

        normalized.append(
            {
                "id": it.get("id") or f"{topic}:{i}:{title[:40]}",
                "title": title,
                "link": link,
                "source": it.get("source") or it.get("publisher") or "Source",
                "summary": it.get("summary") or it.get("description") or "",
                "publishedAt": it.get("publishedAt") or it.get("published") or "",
                "topic": it.get("topic") or topic,
            }
        )

    return {"items": normalized, "meta": {"topic": topic, "query": q, "total": len(normalized)}}
