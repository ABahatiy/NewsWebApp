import os
import json
import requests
from typing import Any, Dict, List, Optional


class LlmAgent:
    """
    Мінімальний агент через OpenAI REST API без залежності від openai SDK.
    Працює на Render: потрібен OPENAI_API_KEY в Environment.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_sec: Optional[float] = None,
        max_input_chars: Optional[int] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        self.model = model if model is not None else os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.timeout_sec = float(timeout_sec if timeout_sec is not None else os.getenv("OPENAI_TIMEOUT_SEC", "25"))
        self.max_input_chars = int(max_input_chars if max_input_chars is not None else os.getenv("LLM_MAX_INPUT_CHARS", "3500"))

    def _trim(self, text: str) -> str:
        text = text or ""
        if len(text) <= self.max_input_chars:
            return text
        # обрізаємо, але зберігаємо кінець (часто там питання)
        return text[-self.max_input_chars :]

    def _build_messages(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        extra_context: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        system = (
            "Ти корисний асистент новинного застосунку. "
            "Відповідай стисло та по суті. "
            "Якщо бракує даних — став уточнювальне питання. "
            "Не вигадуй факти."
        )
        if extra_context:
            system += f"\n\nКонтекст:\n{extra_context}"

        msgs: List[Dict[str, str]] = [{"role": "system", "content": system}]

        if history:
            # history очікуємо як список: [{"role":"user"/"assistant","content":"..."}]
            for m in history[-20:]:
                r = (m.get("role") or "").strip()
                c = (m.get("content") or "").strip()
                if r in ("user", "assistant") and c:
                    msgs.append({"role": r, "content": self._trim(c)})

        msgs.append({"role": "user", "content": self._trim(user_message)})
        return msgs

    def ask(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
        extra_context: Optional[str] = None,
    ) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        url = "https://api.openai.com/v1/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": self._build_messages(user_message, history=history, extra_context=extra_context),
            "temperature": 0.4,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=self.timeout_sec)
        if resp.status_code >= 400:
            raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")

        data = resp.json()
        return (data["choices"][0]["message"]["content"] or "").strip()
