# ai_agent.py
import html as html_lib
import re
from typing import Dict, List

TAG_RE = re.compile(r"<[^>]+>")


def _clean(s: str) -> str:
    if not s:
        return ""
    s = TAG_RE.sub("", s)
    s = html_lib.unescape(s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def summarize_news_item(item: Dict, keywords: List[str]) -> str:
    title = _clean(item.get("title", ""))
    summary = _clean(item.get("summary", ""))
    link = item.get("link", "")
    topic = item.get("topic", "")

    if summary:
        return f"{topic}\n{title}\n{summary}\n{link}"
    return f"{topic}\n{title}\n{link}"
