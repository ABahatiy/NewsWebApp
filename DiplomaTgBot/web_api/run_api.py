from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
import feedparser
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from config import (
    TOPICS,
    NEWS_SOURCES,
    REQUEST_TIMEOUT,
    MAX_ITEMS_TOTAL,
    MAX_FETCH_DURATION_SEC,
    CORS_ORIGINS,
)
from llm_agent import chat_with_agent

app = FastAPI(title="Diploma News API", version="1.0")

# --- CORS ---
if CORS_ORIGINS == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "Diploma News API",
        "status": "ok",
        "endpoints": ["/health", "/topics", "/news?topic=all&limit=10", "/chat"],
    }

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/topics")
def get_topics() -> Dict[str, Any]:
    # формат під фронт (id/title)
    topics = [{"id": t["key"], "title": t["label"], "keywords": []} for t in TOPICS]
    return {"topics": topics}

def _pick_sources(topic_key: str) -> List[Dict[str, Any]]:
    if topic_key == "all":
        return NEWS_SOURCES
    return [s for s in NEWS_SOURCES if s.get("key") == topic_key]

def _extract_best_link(entry: Any) -> str:
    # feedparser зазвичай дає entry.link
    link = (getattr(entry, "link", "") or "").strip()
    if link:
        return link
    # інколи буває links[]
    links = getattr(entry, "links", None)
    if links and isinstance(links, list):
        for l in links:
            href = (l.get("href") or "").strip()
            if href:
                return href
    return ""

def _extract_summary(entry: Any) -> str:
    # Google News RSS часто має summary/detail в HTML
    summary = (getattr(entry, "summary", "") or "").strip()
    if summary:
        return summary
    return (getattr(entry, "description", "") or "").strip()

def _extract_published(entry: Any) -> str:
    # намагаємось витягнути published
    published = (getattr(entry, "published", "") or "").strip()
    if published:
        return published
    return ""

@app.get("/news")
def get_news(
    topic: str = Query("all"),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    topic_key = (topic or "all").strip().lower()
    sources = _pick_sources(topic_key)

    started = time.time()
    items: List[Dict[str, Any]] = []

    for src in sources:
        if len(items) >= min(limit, MAX_ITEMS_TOTAL):
            break

        if (time.time() - started) > MAX_FETCH_DURATION_SEC:
            break

        url = src.get("url", "")
        if not url:
            continue

        try:
            r = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            feed = feedparser.parse(r.text)

            for e in feed.entries:
                if len(items) >= min(limit, MAX_ITEMS_TOTAL):
                    break

                title = (getattr(e, "title", "") or "").strip()
                link = _extract_best_link(e)
                summary = _extract_summary(e)
                published = _extract_published(e)

                # мінімальний захист від порожніх записів
                if not title:
                    continue

                items.append(
                    {
                        "id": getattr(e, "id", "") or link or title,
                        "title": title,
                        "link": link,
                        "source": src.get("topic") or src.get("key") or "",
                        "summary": summary,
                        "publishedAt": published,
                        "topic": src.get("key") or "",
                    }
                )

        except Exception:
            # пропускаємо проблемне джерело, щоб API не падав
            continue

    meta = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "total": len(items),
        "topic": topic_key,
    }

    return {"items": items[:limit], "topics": [{"id": t["key"], "title": t["label"], "keywords": []} for t in TOPICS], "meta": meta}

@app.post("/chat")
def chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Очікуємо payload:
      {
        "message": "..."
        "history": [{"role":"user|assistant","content":"..."}]  # опційно
      }
    """
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []
    result = chat_with_agent(message=message, history=history)
    return result
