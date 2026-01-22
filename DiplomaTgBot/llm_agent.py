# llm_agent.py

import logging
import json
from typing import Dict, List, Tuple

from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SEC,
    LLM_MAX_INPUT_CHARS,
    DIGEST_MAX_CHARS,
)

logger = logging.getLogger(__name__)


def _ensure_key() -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY не заданий.")


def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def select_relevant_items_with_llm(items: List[Dict], keywords: List[str], max_keep: int = 6) -> List[Dict]:
    if not keywords:
        return items[:max_keep]

    _ensure_key()
    client = OpenAI(api_key=OPENAI_API_KEY)

    kw = ", ".join(keywords)

    lines: List[str] = []
    for i, it in enumerate(items, start=1):
        title = _truncate(it.get("title", ""), 160)
        summary = _truncate(it.get("summary", ""), 220)
        link = it.get("link", "")
        lines.append(f"{i}. {title}\nОпис: {summary}\nURL: {link}")

    raw = "\n\n".join(lines)
    raw = _truncate(raw, LLM_MAX_INPUT_CHARS)

    prompt = f"""
Ключові слова: {kw}

Обери лише ті пункти, які дійсно відповідають ключовим словам.
Відкинь хибні збіги (наприклад, коли ключове слово є частиною іншого слова).

Поверни відповідь СТРОГО у форматі JSON-масиву номерів, наприклад: [2,5,6]
Максимум {max_keep} пунктів.

Список новин:
{raw}
""".strip()

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Відповідай строго у потрібному форматі."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        timeout=OPENAI_TIMEOUT_SEC,
    )

    content = (resp.choices[0].message.content or "").strip()

    try:
        idxs = json.loads(content)
        if not isinstance(idxs, list):
            raise ValueError("Not a list")
        idxs = [int(x) for x in idxs if str(x).isdigit()]
    except Exception as exc:
        logger.warning("Не вдалося розпарсити JSON від LLM (%s). Відповідь: %s", exc, content)
        return items[:max_keep]

    chosen: List[Dict] = []
    for i in idxs:
        if 1 <= i <= len(items):
            chosen.append(items[i - 1])
        if len(chosen) >= max_keep:
            break

    return chosen or items[:max_keep]


def build_digest_with_llm(items: List[Dict], keywords: List[str]) -> str:
    """
    ВАЖЛИВО: повертаємо HTML (короткі лінки через <a href="">Детальніше</a>)
    """
    _ensure_key()
    client = OpenAI(api_key=OPENAI_API_KEY)

    kw = ", ".join(keywords) if keywords else "без фільтра"

    lines: List[str] = []
    for i, it in enumerate(items, start=1):
        title = _truncate(it.get("title", ""), 160)
        summary = _truncate(it.get("summary", ""), 240)
        link = it.get("link", "")
        topic = it.get("topic", "")
        lines.append(
            f"{i}) Тема: {topic}\nЗаголовок: {title}\nОпис: {summary}\nURL: {link}"
        )

    raw = "\n\n".join(lines)
    raw = _truncate(raw, LLM_MAX_INPUT_CHARS)

    prompt = f"""
Ти — програмний агент моніторингу новин. Зроби короткий дайджест українською у форматі HTML для Telegram.

Вимоги:
- 1 повідомлення, до {DIGEST_MAX_CHARS} символів.
- 4–6 пунктів максимум.
- Кожен пункт: 1 коротке речення по суті + короткий лінк
- Лінк роби ТІЛЬКИ так: <a href="URL">Детальніше</a>
- НІКОЛИ не показуй сам URL текстом (щоб не було великих посилань)
- Не використовуй Markdown
- Не вигадуй фактів

Ключові слова: {kw}

Новини:
{raw}
""".strip()

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Поверни лише HTML-текст для Telegram, без пояснень."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        timeout=OPENAI_TIMEOUT_SEC,
    )

    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("LLM повернув порожню відповідь")

    return _truncate(text, DIGEST_MAX_CHARS)


def chat_with_llm(history: List[Tuple[str, str]], user_text: str) -> str:
    _ensure_key()
    client = OpenAI(api_key=OPENAI_API_KEY)

    messages = [
        {
            "role": "system",
            "content": (
                "Ти чат-асистент новинного бота. "
                "Відповідай українською, коротко і по суті. "
                "Якщо користувач питає про налаштування — пояснюй, що можна робити через кнопки."
            ),
        }
    ]

    for role, content in history:
        r = "assistant" if role == "assistant" else "user"
        messages.append({"role": r, "content": content})

    messages.append({"role": "user", "content": user_text})

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.5,
        timeout=OPENAI_TIMEOUT_SEC,
    )

    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("LLM повернув порожню відповідь")
    return text
