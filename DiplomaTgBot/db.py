# db.py

import sqlite3
from typing import Iterator

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """
    Повертає нове зʼєднання з базою даних.
    Відкриваємо окреме зʼєднання для кожної операції – простіше і безпечніше
    для багатопотоковості у випадку з невеликим ботом.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Створює таблиці, якщо вони ще не існують."""
    conn = get_connection()
    cur = conn.cursor()

    # Таблиця користувачів
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            chat_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            last_name   TEXT,
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Таблиця налаштувань (ключові слова тощо)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            chat_id     INTEGER PRIMARY KEY,
            keywords    TEXT
        );
        """
    )

    # Таблиця вже надісланих новин (щоб не дублювати)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_links (
            chat_id     INTEGER NOT NULL,
            link        TEXT    NOT NULL,
            PRIMARY KEY (chat_id, link)
        );
        """
    )

    conn.commit()
    conn.close()


def iter_rows(query: str, params: tuple = ()) -> Iterator[sqlite3.Row]:
    """
    Допоміжна функція для ітерації по результатах SELECT.
    Використовується там, де треба пройтись по багатьох рядках.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        for row in cur:
            yield row
    finally:
        conn.close()
