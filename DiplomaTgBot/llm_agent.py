from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

# Підтримка запуску як package і як "root dir = DiplomaTgBot"
try:
    from .config import OPENAI_API_KEY
except Exception:
    from config import OPENAI_API_KEY  # type: ignore


def _fallback_response(message: str) -> str:
    # Якщо LLM вимкнено або нема ключа
    return (
        "AI-агент тимчасово недоступний. "
        "Перевір OPENAI_API_KEY / USE_LLM у Render Environment. "
        f"Твоє повідомлення: {message}"
    )


def chat_with_agent(
    message: str,
    context: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Мінімальна функція, яку викликає API.
    context можна передати як список новин (title/source/url/description) — опційно.
    """
    use_llm = os.getenv("USE_LLM", "1").strip().lower() in ("1", "true", "yes", "on")
    if not use_llm or not OPENAI_API_KEY:
        return _fallback_response(message)

    # Найпростіша інтеграція через OpenAI SDK (якщо він у requirements).
    # Якщо SDK у тебе інший/відсутній — бек не впаде, а піде у fallback.
    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return _fallback_response(message)

    client = OpenAI(api_key=OPENAI_API_KEY)

    sys = (
        "Ти AI-помічник новинного агрегатора. "
        "Відповідай коротко, по суті, українською. "
        "Якщо є контекст новин — спирайся на нього."
    )

    ctx_text = ""
    if context:
        lines = []
        for i, it in enumerate(context[:10], start=1):
            title = (it.get("title") or "").strip()
            source = (it.get("source") or "").strip()
            url = (it.get("url") or it.get("link") or "").strip()
            lines.append(f"{i}. {title} ({source}) {url}".strip())
        ctx_text = "\n".join(lines)

    user = message.strip()
    if ctx_text:
        user = f"Ось контекст новин:\n{ctx_text}\n\nЗапит користувача:\n{message.strip()}"

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        return (resp.choices[0].message.content or "").strip() or "Нема відповіді."
    except Exception:
        return _fallback_response(message)
