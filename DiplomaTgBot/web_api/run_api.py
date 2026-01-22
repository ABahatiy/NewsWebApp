import os
import time
import logging
from typing import Optional, Dict, Any, List

import requests
import feedparser
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import (
    setup_logging,
    REQUEST_TIMEOUT,
    MAX_ITEMS_TOTAL,
    TOPICS,
    get_topic_by_key,
    NEWS_SOURCES,
)

from llm_agent import chat_with_agent


setup_logging()
logger = logging.getLogger("web_api")

app = FastAPI(title="Diploma News API", version="1.0.0")


# --- CORS ---
# На Render в Environment задай:
# CORS_ORIGINS=https://newswebapp-pied.vercel.app,https://<твій-другий-домен>.vercel.app
cors_origins_raw = os.getenv("CORS_ORIGINS", "").strip()
cors_origins = [x.strip() for x in cors_origins_raw.split(",") if x.strip()]

if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Якщо не задано — лишаємо без CORS (щоб випадково не відкрити всім)
    logger.info("CORS_ORIGINS is empty; CORS middleware is not enabled")


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "status": "ok",
        "hint": "Use /health, /topics, /news, /chat. Docs: /docs",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/topics")
def topics() -> Dict[str, Any]:
    return {"topics": TOPICS}


def _fetch_google_news_rss(url: str, timeout: float) -> List[Dict[str, Any]]:
    """
    Повертає список item'ів із RSS.
    """
    # Google News RSS інколи блокує без User-Agent
    headers = {"User-Agent": "Mozilla/5.0 (NewsWebApp; +https://example.com)"}
    r = requests.get(url, timeout=timeout, headers=headers)
    r.raise_for_status()
    parsed = feedparser.parse(r.text)

    items: List[Dict[str, Any]] = []
    for e in parsed.entries or []:
        title = (getattr(e, "title", "") or "").strip()
        link = (getattr(e, "link", "") or "").strip()
        published = (getattr(e, "published", "") or "").strip()
        summary = (getattr(e, "summary", "") or "").strip()

        if not title or not link:
            continue

        items.append(
            {
                "title": title,
                "url": link,
                "published": published,
                "summary": summary,
            }
        )
    return items


@app.get("/news")
def news(
    topic: str = Query("all", description="topic key from /topics або 'all'"),
    limit: int = Query(10, ge=1, le=60),
) -> Dict[str, Any]:
    """
    topic=all або topic=<key>
    """
    started = time.time()

    try:
        topic = (topic or "").strip().lower()
        if topic != "all":
            t = get_topic_by_key(topic)
            if not t:
                raise HTTPException(status_code=400, detail=f"Unknown topic key: {topic}")

        # Джерела з config.py (NEWS_SOURCES згенерований з TOPICS)
        sources = NEWS_SOURCES
        if topic != "all":
            sources = [s for s in NEWS_SOURCES if s.get("key") == topic]

        if not sources:
            return {"items": [], "count": 0}

        all_items: List[Dict[str, Any]] = []
        for src in sources:
            url = src.get("url")
            if not url:
                continue

            try:
                items = _fetch_google_news_rss(url, timeout=float(REQUEST_TIMEOUT))
                for it in items:
                    it["topic"] = src.get("topic")
                    it["key"] = src.get("key")
                all_items.extend(items)
            except Exception as e:
                # Не валимо весь запит через одну тему, але лог пишемо
                logger.exception("Failed fetching RSS for %s: %s", url, e)

            if len(all_items) >= MAX_ITEMS_TOTAL:
                break

        # просте обрізання
        all_items = all_items[:limit]

        return {
            "items": all_items,
            "count": len(all_items),
            "took_ms": int((time.time() - started) * 1000),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("NEWS endpoint crashed: %s", e)
        raise HTTPException(status_code=500, detail="News fetch failed. Check server logs.")


@app.post("/chat")
def chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Очікує:
    {
      "message": "привіт",
      "history": [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]
    }
    """
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or None
    result = chat_with_agent(message=message, history=history)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "LLM failed"))
    return result
