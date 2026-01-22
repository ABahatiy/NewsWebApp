from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    # коли запускаємо як пакет з кореня репо
    from DiplomaTgBot.config import TOPICS
except ModuleNotFoundError:
    # коли Root Directory = DiplomaTgBot
    from config import TOPICS

app = FastAPI(title="DiplomaTgBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/topics")
def topics():
    return TOPICS
