from __future__ import annotations

from typing import List, Dict

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SEC,
    LLM_MAX_INPUT_CHARS,
    USE_LLM,
    CHAT_HISTORY_LIMIT,
)

def _trim_text(s: str, limit: int) -> str:
    s = (s or "").strip()
    if len(s) <= limit:
        return s
    return s[:limit] + "..."

def _normalize_history(history: List[Dict]) -> List[Dict]:
    cleaned: List[Dict] = []
    for m in history or []:
        role = (m.get("role") or "").strip()
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": content})
    if len(cleaned) > CHAT_HISTORY_LIMIT:
        cleaned = cleaned[-CHAT_HISTORY_LIMIT:]
    return cleaned

def chat_with_agent(message: str, history: List[Dict] | None = None) -> Dict:
    """
    Повертає:
      {
        "answer": "...",
        "model": "...",
        "used_llm": true/false
      }
    """
    msg = _trim_text(message, LLM_MAX_INPUT_CHARS)
    hist = _normalize_history(history or [])

    if not USE_LLM:
        return {
            "answer": "LLM вимкнено (USE_LLM=0).",
            "model": OPENAI_MODEL,
            "used_llm": False,
        }

    if not OPENAI_API_KEY:
        return {
            "answer": "Не задано OPENAI_API_KEY на сервері.",
            "model": OPENAI_MODEL,
            "used_llm": False,
        }

    # максимально проста інтеграція через openai (новий клієнт)
    try:
        from openai import OpenAI
    except Exception:
        return {
            "answer": "Не встановлено бібліотеку openai у requirements.txt.",
            "model": OPENAI_MODEL,
            "used_llm": False,
        }

    client = OpenAI(api_key=OPENAI_API_KEY)

    messages = []
    # системне повідомлення можна мінімальне, щоб не ламати логіку
    messages.append({
        "role": "system",
        "content": "Ти AI-помічник новинного застосунку. Відповідай коротко і по суті українською.",
    })
    messages.extend(hist)
    messages.append({"role": "user", "content": msg})

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            timeout=OPENAI_TIMEOUT_SEC,
        )
        answer = (resp.choices[0].message.content or "").strip()
        if not answer:
            answer = "Порожня відповідь від моделі."
        return {"answer": answer, "model": OPENAI_MODEL, "used_llm": True}
    except Exception as e:
        return {
            "answer": f"Помилка виклику LLM: {type(e).__name__}: {e}",
            "model": OPENAI_MODEL,
            "used_llm": False,
        }
