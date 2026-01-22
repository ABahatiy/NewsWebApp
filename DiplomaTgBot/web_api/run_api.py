from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Підтримка запуску як package і як "root dir = DiplomaTgBot"
try:
    from ..config import TOPICS, RSS_URLS
except Exception:
    from config import TOPICS, RSS_URLS  # type: ignore

try:
    from llm_agent import chat_with_agent
except Exception:
    # якщо імпорт не вдався — не валимо сервіс, просто вимкнемо чат
    chat_with_agent = None  # type: ignore


app = FastAPI(title="Diploma News API", version="1.0.0")

cors_origins = os.getenv("CORS_ORIGINS", "*").strip()
allow_origins = [o.strip() for o in cors_origins.split(",")] if cors_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_last_cache: Dict[str, Any] = {
    "ts": 0.0,
    "topic": "",
    "limit": 0,
    "items": [],
}


class NewsItem(BaseModel):
    title: str
    url: str
    source: str
    description: str = ""
    published_at: str = ""


class NewsResponse(BaseModel):
    items: List[NewsItem]
    meta: Dict[str, Any]


class ChatRequest(BaseModel):
    message: str
    context: Optional[List[Dict[str, Any]]] = None


class ChatResponse(BaseModel):
    answer: str


@app.get("/")
def root() -> Dict[str, Any]:
    # щоб головна сторінка не була пустою/Not Found
    return {"service": "diploma-news", "status": "ok", "endpoints": ["/health", "/topics", "/news", "/chat"]}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/topics")
def topics() -> Dict[str, Any]:
    return {"topics": TOPICS}


def _extract_source_from_title(title: str) -> str:
    # у Google News RSS часто "Заголовок — Джерело"
    if " - " in title:
        return title.split(" - ", 1)[-1].strip()
    if " — " in title:
        return title.split(" — ", 1)[-1].strip()
    return ""


def _fetch_google_rss(url: str, timeout: int = 15) -> List[Dict[str, Any]]:
    # Мінімальний парсер без важких залежностей
    # В RSS Google News часто link = <link>...</link> у item
    import xml.etree.ElementTree as ET

    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()

    root = ET.fromstring(r.text)
    channel = root.find("channel")
    if channel is None:
        return []

    out: List[Dict[str, Any]] = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()

        source = _extract_source_from_title(title)

        out.append(
            {
                "title": title,
                "url": link,  # головне: URL новини
                "source": source,
                "description": desc,
                "published_at": pub,
            }
        )

    return out


@app.get("/news", response_model=NewsResponse)
def news(
    topic: str = Query(default="all"),
    limit: int = Query(default=10, ge=1, le=50),
) -> Dict[str, Any]:
    cache_ttl = int(os.getenv("NEWS_CACHE_TTL", "120"))  # секунд
    now = time.time()

    # простий кеш, щоб Render не дохнув від частих запитів
    if (
        _last_cache["items"]
        and _last_cache["topic"] == topic
        and _last_cache["limit"] == limit
        and now - float(_last_cache["ts"]) < cache_ttl
    ):
        return {
            "items": _last_cache["items"],
            "meta": {
                "fetchedAt": _last_cache.get("fetchedAt", datetime.now(timezone.utc).isoformat()),
                "topic": topic,
                "total": len(_last_cache["items"]),
                "cached": True,
            },
        }

    urls: List[str] = []
    if topic == "all":
        # всі RSS
        for _, v in RSS_URLS.items():
            urls.append(v)
    else:
        if topic not in RSS_URLS:
            return {
                "items": [],
                "meta": {"fetchedAt": datetime.now(timezone.utc).isoformat(), "topic": topic, "total": 0},
            }
        urls = [RSS_URLS[topic]]

    items: List[Dict[str, Any]] = []
    for u in urls:
        try:
            items.extend(_fetch_google_rss(u))
        except Exception:
            continue

    # прибираємо порожні url, і ріжемо
    items = [it for it in items if (it.get("url") or "").strip()]
    items = items[:limit]

    fetched_at = datetime.now(timezone.utc).isoformat()

    _last_cache.update(
        {
            "ts": now,
            "topic": topic,
            "limit": limit,
            "items": items,
            "fetchedAt": fetched_at,
        }
    )

    return {
        "items": items,
        "meta": {"fetchedAt": fetched_at, "topic": topic, "total": len(items), "cached": False},
    }


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> Dict[str, Any]:
    if chat_with_agent is None:
        return {"answer": "AI-агент недоступний (помилка імпорту llm_agent)."}
    answer = chat_with_agent(payload.message, payload.context)
    return {"answer": answer}
