import os
from typing import List, Dict, Any, Optional

import requests
import feedparser
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..config import (
    TOPICS,
    get_topic_by_key,
    NEWS_SOURCES,
    REQUEST_TIMEOUT,
    MAX_ITEMS_TOTAL,
)
from ..llm_agent import LlmAgent


def _env_list(name: str, default: str = "") -> List[str]:
    raw = os.getenv(name, default) or ""
    items = [x.strip() for x in raw.split(",") if x.strip()]
    return items


def _pick_source_urls(topic_key: str) -> List[str]:
    # topic_key може бути: конкретний ключ або "all"
    if topic_key == "all":
        return [s["url"] for s in NEWS_SOURCES if s.get("url")]

    urls = []
    for s in NEWS_SOURCES:
        if s.get("key") == topic_key and s.get("url"):
            urls.append(s["url"])
    return urls


def _fetch_rss(url: str, timeout: float) -> List[Dict[str, Any]]:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "NewsWebApp/1.0"})
    r.raise_for_status()

    feed = feedparser.parse(r.text)
    items: List[Dict[str, Any]] = []

    for e in feed.entries or []:
        title = (getattr(e, "title", "") or "").strip()
        link = (getattr(e, "link", "") or "").strip()
        published = (getattr(e, "published", "") or "").strip()

        if not title or not link:
            continue

        items.append(
            {
                "title": title,
                "link": link,
                "published": published,
                "source": "Google News",
            }
        )
    return items


def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for it in items:
        key = (it.get("link") or it.get("title") or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _build_context_from_news(news_items: List[Dict[str, Any]], limit: int = 8) -> str:
    lines = []
    for i, n in enumerate(news_items[:limit], start=1):
        t = (n.get("title") or "").strip()
        l = (n.get("link") or "").strip()
        if t and l:
            lines.append(f"{i}. {t}\n{l}")
    return "\n\n".join(lines)


app = FastAPI(title="Diploma News API", version="1.0.0")

# CORS: дозволяємо фронту з Vercel звертатись до Render
# Приклад: CORS_ORIGINS=https://newswebapp-pied.vercel.app,https://*.vercel.app
cors_origins = _env_list("CORS_ORIGINS", "")
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # якщо не задано — відкриваємо для всіх (на старті зручно), потім краще обмежити
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

agent = LlmAgent()


class ChatMessage(BaseModel):
    role: str = Field(..., description="user або assistant")
    content: str = Field(..., description="Текст повідомлення")


class ChatRequest(BaseModel):
    message: str = Field(..., description="Повідомлення користувача")
    history: Optional[List[ChatMessage]] = Field(default=None, description="Історія чату")
    topic: str = Field(default="all", description="Ключ теми або all")
    limit: int = Field(default=10, description="Скільки новин брати у контекст")


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "Diploma News API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/topics")
def topics() -> List[Dict[str, str]]:
    return [{"key": t["key"], "label": t["label"]} for t in TOPICS]


@app.get("/news")
def news(
    topic: str = Query("all", description="Ключ теми або all"),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    topic = (topic or "all").strip().lower()
    if topic != "all" and not get_topic_by_key(topic):
        return {"items": [], "topic": topic, "error": "Unknown topic"}

    urls = _pick_source_urls(topic)
    all_items: List[Dict[str, Any]] = []

    # щоб не “вмерти” по часу — при all беремо обмеження загальних елементів
    hard_cap = min(MAX_ITEMS_TOTAL, 200)

    for url in urls:
        try:
            all_items.extend(_fetch_rss(url, timeout=REQUEST_TIMEOUT))
        except Exception:
            # не валимо весь запит через одне джерело
            continue

        if len(all_items) >= hard_cap:
            break

    all_items = _dedupe(all_items)
    return {"items": all_items[:limit], "topic": topic, "count": len(all_items[:limit])}


@app.post("/agent/chat")
def agent_chat(payload: ChatRequest) -> Dict[str, Any]:
    topic = (payload.topic or "all").strip().lower()
    if topic != "all" and not get_topic_by_key(topic):
        topic = "all"

    # Беремо новини і даємо агенту як контекст (коротко)
    urls = _pick_source_urls(topic)
    all_items: List[Dict[str, Any]] = []
    hard_cap = 60

    for url in urls:
        try:
            all_items.extend(_fetch_rss(url, timeout=REQUEST_TIMEOUT))
        except Exception:
            continue
        if len(all_items) >= hard_cap:
            break

    all_items = _dedupe(all_items)
    context = _build_context_from_news(all_items, limit=min(max(payload.limit, 1), 20))

    history = []
    if payload.history:
        history = [{"role": m.role, "content": m.content} for m in payload.history]

    result = agent.chat(
        message=payload.message,
        history=history,
        context=context,
    )

    return {
        "answer": result.get("answer"),
        "used_llm": result.get("used_llm", False),
        "model": result.get("model"),
        "topic": topic,
    }
