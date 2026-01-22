import os
from typing import List, Dict, Any, Optional

from .config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SEC,
    USE_LLM,
    LLM_MAX_INPUT_CHARS,
    CHAT_HISTORY_LIMIT,
)

# Працюємо з OpenAI SDK v1.x
# requirements.txt має містити: openai>=1.0.0
try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _trim(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


class LlmAgent:
    def __init__(self) -> None:
        self.enabled = bool(USE_LLM) and bool(OPENAI_API_KEY) and (OpenAI is not None)
        self.model = OPENAI_MODEL
        self.timeout = OPENAI_TIMEOUT_SEC

        self._client = None
        if self.enabled:
            self._client = OpenAI(api_key=OPENAI_API_KEY)

        self.system_prompt = (
            "Ти — корисний, лаконічний і точний асистент новинного вебзастосунку. "
            "Відповідай українською. Якщо користувач просить поради по новинах — "
            "пояснюй коротко суть, контекст і можливі наслідки. "
            "Не вигадуй фактів: якщо даних не вистачає — скажи про це і запропонуй, "
            "що уточнити."
        )

    def is_ready(self) -> bool:
        return self.enabled

    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        context: str = "",
    ) -> Dict[str, Any]:
        """
        history: список у форматі [{"role":"user"|"assistant", "content":"..."}]
        context: додатковий контекст (наприклад, підбірка новин)
        """
        message = (message or "").strip()
        if not message:
            return {"answer": "Напиши повідомлення, і я відповім.", "used_llm": False}

        if not self.is_ready():
            # М’який фолбек, щоб фронт не падав
            reason = []
            if not USE_LLM:
                reason.append("USE_LLM=0")
            if not OPENAI_API_KEY:
                reason.append("OPENAI_API_KEY не заданий")
            if OpenAI is None:
                reason.append("пакет openai не встановлено")
            why = ", ".join(reason) if reason else "LLM вимкнено"
            return {
                "answer": f"ШІ-агент зараз недоступний ({why}).",
                "used_llm": False,
            }

        safe_history: List[Dict[str, str]] = []
        if history:
            # беремо останні N повідомлень
            history = history[-CHAT_HISTORY_LIMIT:]
            for item in history:
                r = (item.get("role") or "").strip()
                c = (item.get("content") or "").strip()
                if r in ("user", "assistant") and c:
                    safe_history.append({"role": r, "content": _trim(c, 1500)})

        ctx = _trim(context, 4000)
        user_text = message
        if ctx:
            user_text = (
                "Контекст (новини/дані):\n"
                f"{ctx}\n\n"
                "Запит користувача:\n"
                f"{message}"
            )

        # обмежуємо загальний інпут
        user_text = _trim(user_text, LLM_MAX_INPUT_CHARS)

        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(safe_history)
        messages.append({"role": "user", "content": user_text})

        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            timeout=self.timeout,
        )

        answer = ""
        try:
            answer = resp.choices[0].message.content or ""
        except Exception:
            answer = ""

        answer = (answer or "").strip() or "Не зміг сформувати відповідь. Спробуй перефразувати."
        return {"answer": answer, "used_llm": True, "model": self.model}
