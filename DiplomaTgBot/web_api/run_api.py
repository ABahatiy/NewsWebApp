import os
import re
from typing import Any, Dict, List, Optional

import feedparser
import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ВАЖЛИВО: імпорт без відносних шляхів, щоб працювало на Render з uvicorn web_api.run_api:app
import config
from llm_agent import chat_with_agent


app = FastAPI(title="Diploma News API", version="1.0.0")


def _parse_origins(value: str) -> List[str]:
    value = (value or "").strip()
    if not value:
        return []
    # дозволяємо "a,b,c" або "a; b; c"
    parts = re.split(r"[;,]\s*", value)
    return [p.strip() for p in parts if p.strip()]


CORS_ORIGINS = _parse_origins(os.getenv("CORS_ORIGINS", ""))

# Якщо не задав — дозволимо все (так простіше на старті). Потім краще обмежити.
if CORS_ORIGINS:
    allow_origins = CORS_ORIGINS
    allow_credentials = True
else:
    allow_origins = ["*"]
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewsItem(BaseModel):
    title: str
    url: str
    source: str = ""
    description: str = ""


class NewsResponse(BaseModel):
    items: List[NewsItem]
    updated_at: str = ""


class ChatRequest(BaseModel):
    message: str
    # опціонально фронт може передати поточні новини як контекст
    context_items: Optional[List[Dict[str, Any]]] = None


class ChatResponse(BaseModel):
    answer: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/topics")
def topics() -> Dict[str, Any]:
    # topics береться з config.TOPICS
    return {"topics": config.TOPICS}


def _google_news_rss_url(query: str, lang: str = "uk", region: str = "UA") -> str:
    from urllib.parse import quote

    q = quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={region}&ceid={region}:{lang}"


def _clean_html(text: str) -> str:
    if not text:
        return ""
    # грубо прибираємо теги, щоб не “їхала” верстка на фронті
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"\s+", " ", text).strip()
    return text


@app.get("/news", response_model=NewsResponse)
async def news(
    topic: str = Query(default="all"),
    limit: int = Query(default=10, ge=1, le=50),
) -> NewsResponse:
    topic = (topic or "all").strip().lower()

    # topic=all -> беремо кілька тем, але обмежуємо загальний ліміт
    if topic == "all":
        selected = config.TOPICS[:]
    else:
        found = config.get_topic_by_key(topic)
        selected = [found] if found else []

    if not selected:
        return NewsResponse(items=[], updated_at="")

    # збираємо RSS URL-и
    urls = []
    for t in selected:
        urls.append(_google_news_rss_url(t["query"]))

    timeout = httpx.Timeout(config.REQUEST_TIMEOUT)

    items: List[NewsItem] = []
    updated_at = ""

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for rss_url in urls:
            try:
                r = await client.get(rss_url)
                r.raise_for_status()
                feed = feedparser.parse(r.text)

                if not updated_at:
                    updated_at = getattr(feed.feed, "updated", "") or ""

                for e in feed.entries:
                    title = _clean_html(getattr(e, "title", "") or "")
                    link = getattr(e, "link", "") or ""
                    summary = _clean_html(getattr(e, "summary", "") or "")

                    source = ""
                    # інколи Google News дає source в e.source.title
                    try:
                        source = getattr(getattr(e, "source", None), "title", "") or ""
                    except Exception:
                        source = ""

                    if title and link:
                        items.append(
                            NewsItem(
                                title=title,
                                url=link,
                                source=source,
                                description=summary,
                            )
                        )

                    if len(items) >= limit:
                        break

                if len(items) >= limit:
                    break

            except Exception:
                # не валимо весь /news, якщо одна тема впала
                continue

    return NewsResponse(items=items[:limit], updated_at=updated_at)


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    answer = await chat_with_agent(payload.message, payload.context_items)
    return ChatResponse(answer=answer)
