import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import TOPICS, NEWS_SOURCES, USE_LLM
from news_fetcher import fetch_news  # має повертати список новин (як у вас уже працює для фронта)
from llm_agent import LlmAgent


app = FastAPI(title="Diploma News API", version="1.0.0")


def _parse_origins(value: str) -> List[str]:
    items = [x.strip() for x in (value or "").split(",")]
    return [x for x in items if x]


# CORS: на Render вкажеш CORS_ORIGINS="https://newswebapp-pied.vercel.app,https://your-domain.vercel.app"
cors_origins = _parse_origins(os.getenv("CORS_ORIGINS", ""))
if not cors_origins:
    # якщо не задано — дозволяємо все (для дебагу). Для продакшену краще задати CORS_ORIGINS.
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
    # опціонально: можна передати короткий контекст (наприклад, список 3–5 новин)
    context: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    model: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/topics")
def topics() -> Dict[str, Any]:
    return {"topics": TOPICS}


@app.get("/news")
def news(
    topic: str = Query("all", description="topic key або all"),
    limit: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    """
    Повертає новини з Google News RSS.
    topic:
      - all
      - або конкретний key з TOPICS/NEWS_SOURCES (ukraine, world, ...)
    """
    items = fetch_news(topic=topic, limit=limit, sources=NEWS_SOURCES)
    return {"items": items, "topic": topic, "limit": limit}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """
    ШІ-чат. Ключ OpenAI зберігається на Render (OPENAI_API_KEY).
    """
    if not USE_LLM:
        return ChatResponse(reply="LLM вимкнено на сервері (USE_LLM=0).", model=os.getenv("OPENAI_MODEL", ""))

    agent = LlmAgent()

    history = None
    if req.history:
        history = [{"role": m.role, "content": m.content} for m in req.history]

    reply = agent.ask(
        user_message=req.message,
        history=history,
        extra_context=req.context,
    )
    return ChatResponse(reply=reply, model=agent.model)
