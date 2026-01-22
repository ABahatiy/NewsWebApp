from __future__ import annotations

from typing import Any, Dict, List

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SEC,
    USE_LLM,
    LLM_MAX_INPUT_CHARS,
)

def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."

def _format_news_context(news_items: List[Dict[str, Any]], max_chars: int) -> str:
    # Формуємо компактний контекст для LLM (без полотна лінків)
    parts: List[str] = []
    for i, it in enumerate(news_items or [], start=1):
        title = (it.get("title") or "").strip()
        source = (it.get("source") or it.get("publisher") or "").strip()
        published = (it.get("published") or it.get("date") or "").strip()
        line = f"{i}. {title}"
        meta = " · ".join([x for x in [source, published] if x])
        if meta:
            line += f" ({meta})"
        parts.append(line)

    ctx = "\n".join(parts).strip()
    return _truncate(ctx, max_chars)

def chat_with_agent(user_message: str, news_items: List[Dict[str, Any]]) -> str:
    """
    Повертає відповідь агента. Якщо USE_LLM=0 або немає ключа — дає просту відповідь-заглушку.
    """
    user_message = (user_message or "").strip()
    if not user_message:
        return ""

    # Якщо LLM вимкнено або нема ключа — повертаємо "fallback"
    if (not USE_LLM) or (not OPENAI_API_KEY):
        return "AI агент зараз вимкнений (USE_LLM=0) або не задано OPENAI_API_KEY."

    context = _format_news_context(news_items, max_chars=LLM_MAX_INPUT_CHARS)

    system_prompt = (
        "Ти — новинний помічник. Відповідай українською, лаконічно та по суті. "
        "Якщо питання стосується новин — спирайся на наданий список новин. "
        "Якщо даних недостатньо — скажи, чого не вистачає, і запропонуй уточнення."
    )

    user_prompt = (
        f"Питання користувача:\n{user_message}\n\n"
        f"Ось актуальні новини (для контексту):\n{context}"
    )

    # OpenAI SDK (новий стиль). Якщо у тебе інший SDK/версія — скажеш, піджену.
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        timeout=OPENAI_TIMEOUT_SEC,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return (resp.choices[0].message.content or "").strip()
