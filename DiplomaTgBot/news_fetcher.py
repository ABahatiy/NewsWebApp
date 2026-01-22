# news_fetcher.py

from __future__ import annotations

import logging
import re
import time
import html as html_lib
from typing import List, Dict, Optional

import requests
import feedparser

from config import (
    NEWS_SOURCES,
    REQUEST_TIMEOUT,
    MAX_ITEMS_TOTAL,
    MAX_FETCH_DURATION_SEC,
)

logger = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")


def normalize_keywords(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r"[,\n;]+", text)
    return [p.strip().lower() for p in parts if p.strip()]


def _clean_text(s: str) -> str:
    if not s:
        return ""
    s = TAG_RE.sub("", s)
    s = html_lib.unescape(s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _compile_keyword_patterns(keywords: List[str]) -> List[tuple[str, re.Pattern]]:
    patterns: List[tuple[str, re.Pattern]] = []
    for kw in keywords:
        kw = kw.strip().lower()
        if not kw:
            continue

        if " " in kw:
            pat = re.compile(re.escape(kw), re.IGNORECASE)
        else:
            pat = re.compile(rf"(?<!\w){re.escape(kw)}(?!\w)", re.IGNORECASE)

        patterns.append((kw, pat))
    return patterns


def _match_keywords(item: Dict, patterns: List[tuple[str, re.Pattern]]) -> bool:
    if not patterns:
        return True

    haystack = " ".join(
        [
            str(item.get("title", "")),
            str(item.get("summary", "")),
            str(item.get("content", "")),
        ]
    ).lower()

    return any(p.search(haystack) for _, p in patterns)


def _fetch_rss(url: str) -> Optional[feedparser.FeedParserDict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DiplomaNewsBot/1.0)",
        "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception as exc:
        logger.warning("Не вдалося отримати RSS %s: %s", url, exc)
        return None


def fetch_news(
    keywords: List[str],
    limit_per_feed: int = 6,
    ignore_keywords: bool = False,
    selected_topics: Optional[List[str]] = None,
) -> List[Dict]:
    start = time.time()
    collected: List[Dict] = []

    patterns = [] if ignore_keywords else _compile_keyword_patterns(keywords)
    selected = {t.strip().lower() for t in (selected_topics or []) if t.strip()}

    for src in NEWS_SOURCES:
        if time.time() - start > MAX_FETCH_DURATION_SEC:
            logger.info("Досягнуто ліміт часу збору (%s сек).", MAX_FETCH_DURATION_SEC)
            break

        if src.get("type") != "google_news_rss":
            continue

        # Фільтр по темах: якщо теми обрані — беремо лише їх
        src_key = (src.get("key") or "").strip().lower()
        if selected and src_key not in selected:
            continue

        url = src.get("url")
        topic = src.get("topic", "Тема")
        query = src.get("query", "")

        feed = _fetch_rss(url)
        if not feed or not getattr(feed, "entries", None):
            continue

        count = 0
        for e in feed.entries:
            if count >= limit_per_feed:
                break

            title = _clean_text(getattr(e, "title", "") or "")
            summary = _clean_text(getattr(e, "summary", "") or "")
            link = getattr(e, "link", "") or ""

            item = {
                "source": "Google News",
                "topic": topic,
                "query": query,
                "title": title,
                "summary": summary,
                "content": "",
                "link": link,
            }

            if ignore_keywords or _match_keywords(item, patterns):
                collected.append(item)
                count += 1

            if len(collected) >= MAX_ITEMS_TOTAL:
                break

        if len(collected) >= MAX_ITEMS_TOTAL:
            break

    # Унікалізація по link
    seen = set()
    unique: List[Dict] = []
    for item in collected:
        link = item.get("link", "")
        if link and link in seen:
            continue
        seen.add(link)
        unique.append(item)

    return unique
