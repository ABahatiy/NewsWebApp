import os
from typing import List, Dict, Any

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SEC,
    LLM_MAX_INPUT_CHARS,
    USE_LLM,
)

# Підтримка нового SDK OpenAI (openai>=1.x)
# Якщо бібліотеки нема або ключа нема — агент буде працювати як заглушка.
def _is_llm_ready() -> bool:
    return bool(USE_LLM and OPENAI_API_KEY)


def _truncate(text: str, limit: int) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit]


def chat_with_agent(message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
    """
    message: поточне повідомлення користувача
    history: список повідомлень формату [{"role":"user|assistant","content":"..."}]
    """
    message = (message or "").strip()
    if not message:
        return {"ok": False, "error": "Empty message"}

    if not _is_llm_ready():
        return {
            "ok": True,
            "mode": "stub",
            "reply": "LLM вимкнено або не задано OPENAI_API_KEY на бекенді.",
        }

    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return {
            "ok": True,
            "mode": "stub",
            "reply": "На бекенді не встановлено бібліотеку openai. Додай її в requirements.txt.",
        }

    client = OpenAI(api_key=OPENAI_API_KEY)

    safe_history: List[Dict[str, str]] = []
    if history:
        for m in history[-20:]:
            role = (m.get("role") or "").strip()
            content = (m.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                safe_history.append({"role": role, "content": _truncate(content, 1200)})

    user_text = _truncate(message, LLM_MAX_INPUT_CHARS)

    system = (
        "Ти ШІ-асистент новинного застосунку. Відповідай стисло, по суті. "
        "Якщо користувач просить підсумувати новини — попроси вставити текст/посилання або "
        "запропонуй короткий формат підсумку."
    )

    messages = [{"role": "system", "content": system}] + safe_history + [{"role": "user", "content": user_text}]

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            timeout=OPENAI_TIMEOUT_SEC,
        )
        reply = resp.choices[0].message.content or ""
        return {"ok": True, "mode": "openai", "reply": reply.strip()}
    except Exception as e:
        return {"ok": False, "error": f"OpenAI request failed: {type(e).__name__}: {e}"}
