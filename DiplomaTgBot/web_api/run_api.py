from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import time

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from DiplomaTgBot.config import TOPICS
from DiplomaTgBot.news_fetcher import fetch_news


app = FastAPI(title="DiplomaTgBot API", version="1.0.0")

# CORS (щоб фронт з Vercel міг ходити в API)
# Якщо хочеш жорстко дозволити тільки Vercel-домен — скажи, я підставлю конкретний.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _topics_payload() -> List[Dict[str, Any]]:
    return [{"id": "all", "title": "Усі", "keywords": []}] + [
        {"id": t["key"], "title": t["label"], "keywords": []} for t in TOPICS
    ]

def _resolve_query(topic: str, q: str) -> str:
    q = (q or "").strip()
    topic = (topic or "all").strip().lower()

    if q:
        return q

    if topic == "all":
        return ""

    for t in TOPICS:
        if t["key"] == topic:
            return t["query"]

    return ""

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "time": int(time.time()),
        "topics": len(TOPICS),
    }

@app.get("/news")
def news(
    topic: str = Query(default="all"),
    q: str = Query(default=""),
    limit: int = Query(default=30, ge=1, le=100),
) -> Dict[str, Any]:
    query = _resolve_query(topic, q)

    items = fetch_news(query=query, limit=limit, topic=topic)

    return {
        "items": items,
        "topics": _topics_payload(),
        "meta": {
            "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total": len(items),
            "topic": topic,
            "query": query,
            "limit": limit,
        },
    }
