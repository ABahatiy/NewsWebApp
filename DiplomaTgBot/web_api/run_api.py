from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from config import (
    TOPICS,
    get_topic_by_key,
)

# Якщо у тебе в проєкті ці модулі є — лишаємо.
# Якщо назви відрізняються — скажи, піджену точно під твою структуру.
from news_fetcher import fetch_news  # має існувати у DiplomaTgBot/
from llm_agent import chat_with_agent  # має існувати у DiplomaTgBot/


app = FastAPI(title="Diploma News API", version="1.0.0")


def _parse_cors_origins() -> List[str]:
    """
    CORS_ORIGINS можна задати:
    - "*"  (не рекомендую для прод)
    - "https://site1.com,https://site2.com"
    - або не задавати (тоді дозволимо Vercel за замовчуванням через "*")
    """
    import os

    raw = (os.getenv("CORS_ORIGINS") or "").strip()
    if not raw:
        # Якщо ти використовуєш Vercel rewrite (/api -> Render), CORS взагалі може не знадобитись.
        # Але залишимо м'яко, щоб прямі запити теж не ламались.
        return ["*"]

    if raw == "*":
        return ["*"]

    return [x.strip() for x in raw.split(",") if x.strip()]


cors_origins = _parse_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/topics")
def topics() -> Dict[str, Any]:
    return {"topics": TOPICS}


@app.get("/news")
def news(
    topic: str = Query(default="all"),
    limit: int = Query(default=10, ge=1, le=100),
) -> Dict[str, Any]:
    # topic=all -> всі теми
    if topic == "all":
        selected_topics = TOPICS
    else:
        t = get_topic_by_key(topic)
        if not t:
            return {"items": [], "error": f"Unknown topic: {topic}"}
        selected_topics = [t]

    items: List[Dict[str, Any]] = fetch_news(selected_topics=selected_topics, limit=limit)
    return {"items": items}


@app.post("/agent/chat")
def agent_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload:
      {
        "message": "текст",
        "topic": "all|ukraine|world|...",
        "limit": 10
      }
    """
    message = (payload.get("message") or "").strip()
    if not message:
        return {"answer": "", "error": "message is required"}

    topic = (payload.get("topic") or "all").strip()
    limit = int(payload.get("limit") or 10)

    # Беремо новини як контекст
    if topic == "all":
        selected_topics = TOPICS
    else:
        t = get_topic_by_key(topic)
        selected_topics = [t] if t else TOPICS

    items = fetch_news(selected_topics=selected_topics, limit=limit)

    answer = chat_with_agent(user_message=message, news_items=items)
    return {"answer": answer, "items": items}
