# utils_text.py

from __future__ import annotations

from typing import List
import html

TELEGRAM_MAX_MESSAGE = 4096


def split_for_telegram(text: str, limit: int = TELEGRAM_MAX_MESSAGE) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []

    if len(text) <= limit:
        return [text]

    parts: List[str] = []
    current = ""

    for line in text.split("\n"):
        candidate = line if not current else current + "\n" + line

        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                parts.append(current)

            while len(line) > limit:
                parts.append(line[:limit])
                line = line[limit:]

            current = line

    if current:
        parts.append(current)

    return parts


def escape_html(text: str) -> str:
    return html.escape(text or "")


def html_link(label: str, url: str) -> str:
    label = escape_html(label)
    url = (url or "").strip()
    if not url:
        return label
    return f'<a href="{url}">{label}</a>'
