import os
from typing import List, Dict, Optional

import httpx


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT_SEC = float(os.getenv("OPENAI_TIMEOUT_SEC", "25"))
USE_LLM = os.getenv("USE_LLM", "1") == "1"

SYSTEM_PROMPT = (
    "Ти корисний ШІ-асистент для новинного сайту. "
    "Відповідай українською, коротко і по суті. "
    "Якщо користувач просить підсумок новини — стисло підсумуй. "
    "Якщо просить пояснення — поясни простими словами."
)


class LLMError(Exception):
    pass


async def _openai_chat(messages: List[Dict[str, str]]) -> str:
    """
    Використовує OpenAI Responses API через HTTP (без SDK), щоб не ловити проблеми з версіями.
    Працює у середовищі Render нормально, якщо задано OPENAI_API_KEY.
    """
    if not OPENAI_API_KEY:
        raise LLMError("OPENAI_API_KEY is missing")

    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "input": messages,
    }

    timeout = httpx.Timeout(OPENAI_TIMEOUT_SEC)

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code >= 400:
            raise LLMError(f"OpenAI error {r.status_code}: {r.text}")

        data = r.json()

    # Витягуємо текст відповіді з output
    # Структура Responses API може бути різною; нижче максимально “живучий” парсер.
    out = data.get("output", [])
    parts: List[str] = []

    for item in out:
        content = item.get("content", [])
        for c in content:
            if c.get("type") == "output_text" and "text" in c:
                parts.append(c["text"])

    text = "\n".join(parts).strip()
    if not text:
        # fallback
        text = (data.get("output_text") or "").strip()

    if not text:
        raise LLMError("Empty response from OpenAI")

    return text


async def chat_with_agent(
    user_message: str,
    context_items: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    context_items: список об'єктів новин (title/url/source/description), які можна підмішати в контекст.
    """
    user_message = (user_message or "").strip()
    if not user_message:
        return "Напиши повідомлення, і я відповім."

    if not USE_LLM:
        return "LLM вимкнено (USE_LLM=0)."

    ctx_text = ""
    if context_items:
        lines = []
        for i, it in enumerate(context_items[:10], start=1):
            title = (it.get("title") or "").strip()
            source = (it.get("source") or it.get("publisher") or "").strip()
            url = (it.get("url") or it.get("link") or "").strip()
            desc = (it.get("description") or it.get("summary") or "").strip()
            lines.append(
                f"{i}) {title}\n"
                f"Джерело: {source}\n"
                f"Посилання: {url}\n"
                f"Опис: {desc}\n"
            )
        if lines:
            ctx_text = "Ось добірка новин (контекст):\n\n" + "\n".join(lines)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    if ctx_text:
        messages.append({"role": "user", "content": ctx_text})

    messages.append({"role": "user", "content": user_message})

    return await _openai_chat(messages)
