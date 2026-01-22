from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import config


def _google_news_rss_url(query: str, lang: str = "uk", region: str = "UA") -> str:
    q = quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={region}&ceid={region}:{lang}"


def _parse_rss(xml_bytes: bytes) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return []

    items: List[Dict[str, Any]] = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source_name = (source_el.text.strip() if source_el is not None and source_el.text else "")

        if not title or not link:
            continue

        items.append(
            {
                "title": title,
                "link": link,
                "published": pub_date,
                "source": source_name,
            }
        )
    return items


def _fetch_rss(url: str) -> List[Dict[str, Any]]:
    r = requests.get(url, timeout=config.REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return _parse_rss(r.content)


app = FastAPI(title="Diploma News API", version="1.0.0")


# CORS: щоб Vercel-фронт міг ходити напряму на Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://newswebapp-pied.vercel.app",
        "https://newsweb-8t2qc95hc-andriibahatiys-projects.vercel.app",
        # якщо будуть ще домени Vercel — можна тимчасово поставити "*" (але краще списком)
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "Diploma News API",
        "status": "ok",
        "endpoints": ["/health", "/topics", "/news?topic=all&limit=10"],
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/topics")
def topics() -> List[Dict[str, str]]:
    # Повертаємо теми для фронта
    return [{"key": t["key"], "label": t["label"]} for t in config.TOPICS]


@app.get("/news")
def news(
    topic: str = Query("all"),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    topic_norm = (topic or "all").strip().lower()

    # Формуємо джерела з config.TOPICS (щоб не залежати від старих sources.py)
    sources = []
    if topic_norm == "all":
        sources = [{"key": t["key"], "label": t["label"], "query": t["query"]} for t in config.TOPICS]
    else:
        t = config.get_topic_by_key(topic_norm)
        if t:
            sources = [{"key": t["key"], "label": t["label"], "query": t["query"]}]
        else:
            return {"topic": topic_norm, "items": [], "error": "unknown_topic"}

    all_items: List[Dict[str, Any]] = []
    for s in sources:
        url = _google_news_rss_url(s["query"])
        try:
            items = _fetch_rss(url)
            for it in items:
                it["topic"] = s["key"]
                it["topicLabel"] = s["label"]
            all_items.extend(items)
        except Exception:
            # не валимо весь запит, якщо одне джерело впало
            continue

        if len(all_items) >= config.MAX_ITEMS_TOTAL:
            break

    # просте обрізання по limit
    return {"topic": topic_norm, "items": all_items[:limit]}
