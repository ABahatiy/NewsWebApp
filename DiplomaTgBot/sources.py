# sources.py
from __future__ import annotations

from urllib.parse import quote_plus

# Мова/регіон для Google News RSS
GOOGLE_NEWS_LANG = "uk"
GOOGLE_NEWS_COUNTRY = "UA"
GOOGLE_NEWS_CEID = "UA:uk"


def build_google_news_rss_url(query: str) -> str:
    """
    RSS пошук Google News за запитом.
    Працює без API ключів.
    """
    q = quote_plus(query)
    return (
        "https://news.google.com/rss/search"
        f"?q={q}&hl={GOOGLE_NEWS_LANG}&gl={GOOGLE_NEWS_COUNTRY}&ceid={GOOGLE_NEWS_CEID}"
    )


# Теми для диплома: можна додавати скільки завгодно.
# Кожен елемент — це "тема" (категорія), за якою бот може шукати.
TOPICS: dict[str, str] = {
    "Україна": "Україна OR Kyiv OR Zelenskyy",
    "Світ": "world news",
    "Політика": "політика OR парламент OR вибори",
    "Економіка": "економіка OR інфляція OR курс OR НБУ",
    "Бізнес": "бізнес OR компанія OR інвестиції OR стартап",
    "Технології": "технології OR AI OR штучний інтелект OR OpenAI OR Google",
    "Кібербезпека": "кібербезпека OR хакери OR витік даних OR malware",
    "Наука": "наука OR дослідження OR відкриття",
    "Здоровʼя": "медицина OR здоров'я OR вакцина OR дослідження",
    "Спорт": "спорт OR футбол OR NBA OR UFC",
    "Кіно": "кіно OR фільм OR Netflix OR Marvel OR trailer",
    "Ігри": "ігри OR gaming OR PlayStation OR Xbox OR Steam OR Dota OR CS2",
}


def get_sources() -> list[dict]:
    """
    Повертає список джерел для news_fetcher.
    Тут ми використовуємо лише Google News RSS, щоб було безкоштовно і стабільно.
    Формат джерела уніфікований (type/url/topic).
    """
    sources: list[dict] = []
    for topic_name, query in TOPICS.items():
        sources.append(
            {
                "type": "google_news_rss",
                "topic": topic_name,
                "query": query,
                "url": build_google_news_rss_url(query),
            }
        )
    return sources
