# storage.py

import sqlite3
from typing import List, Dict, Tuple

from config import DB_PATH, CHAT_HISTORY_LIMIT, AUTO_NEWS_INTERVAL_SEC


class Storage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()
        self._ensure_columns()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as con:
            cur = con.cursor()

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    keywords TEXT DEFAULT '',
                    input_state TEXT DEFAULT '',
                    topics TEXT DEFAULT '',
                    auto_interval_sec INTEGER DEFAULT 0
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sent_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    link TEXT NOT NULL,
                    UNIQUE(chat_id, link)
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            con.commit()

    def _ensure_columns(self) -> None:
        """
        Міграція схеми без видалення bot_data.sqlite3.
        Додає відсутні колонки до users.
        """
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("PRAGMA table_info(users)")
            cols = {row[1] for row in cur.fetchall()}

            if "auto_interval_sec" not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN auto_interval_sec INTEGER DEFAULT 0")
            if "input_state" not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN input_state TEXT DEFAULT ''")
            if "topics" not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN topics TEXT DEFAULT ''")
            if "keywords" not in cols:
                cur.execute("ALTER TABLE users ADD COLUMN keywords TEXT DEFAULT ''")

            con.commit()

    def add_user_if_not_exists(self, chat_id: int) -> None:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO users (chat_id, keywords, input_state, topics, auto_interval_sec) VALUES (?, ?, ?, ?, ?)",
                (chat_id, "", "", "", AUTO_NEWS_INTERVAL_SEC),
            )
            con.commit()

    # ---------- keywords ----------
    def set_keywords(self, chat_id: int, keywords: List[str]) -> None:
        normalized = [k.strip().lower() for k in keywords if k.strip()]
        keywords_str = ",".join(normalized)

        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET keywords = ? WHERE chat_id = ?", (keywords_str, chat_id))
            con.commit()

        self.clear_sent_news(chat_id)

    def clear_keywords(self, chat_id: int) -> None:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET keywords = ? WHERE chat_id = ?", ("", chat_id))
            con.commit()

        self.clear_sent_news(chat_id)

    def get_keywords(self, chat_id: int) -> List[str]:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT keywords FROM users WHERE chat_id = ?", (chat_id,))
            row = cur.fetchone()

        if not row or not row[0]:
            return []
        return [k.strip() for k in row[0].split(",") if k.strip()]

    # ---------- topics ----------
    def set_topics(self, chat_id: int, topics: List[str]) -> None:
        normalized = [t.strip().lower() for t in topics if t.strip()]
        topics_str = ",".join(normalized)

        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET topics = ? WHERE chat_id = ?", (topics_str, chat_id))
            con.commit()

        self.clear_sent_news(chat_id)

    def clear_topics(self, chat_id: int) -> None:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET topics = ? WHERE chat_id = ?", ("", chat_id))
            con.commit()

        self.clear_sent_news(chat_id)

    def get_topics(self, chat_id: int) -> List[str]:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT topics FROM users WHERE chat_id = ?", (chat_id,))
            row = cur.fetchone()

        if not row or not row[0]:
            return []
        return [t.strip() for t in row[0].split(",") if t.strip()]

    # ---------- interval ----------
    def set_auto_interval(self, chat_id: int, interval_sec: int) -> None:
        interval_sec = max(60, int(interval_sec))
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET auto_interval_sec = ? WHERE chat_id = ?", (interval_sec, chat_id))
            con.commit()

    def get_auto_interval(self, chat_id: int) -> int:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT auto_interval_sec FROM users WHERE chat_id = ?", (chat_id,))
            row = cur.fetchone()

        if not row or not row[0]:
            return AUTO_NEWS_INTERVAL_SEC
        return int(row[0])

    # ---------- input state ----------
    def set_input_state(self, chat_id: int, state: str) -> None:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE users SET input_state = ? WHERE chat_id = ?", (state or "", chat_id))
            con.commit()

    def get_input_state(self, chat_id: int) -> str:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT input_state FROM users WHERE chat_id = ?", (chat_id,))
            row = cur.fetchone()

        if not row or not row[0]:
            return ""
        return str(row[0])

    # ---------- users ----------
    def get_all_chat_ids(self) -> List[int]:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT chat_id FROM users")
            rows = cur.fetchall()
        return [r[0] for r in rows]

    # ---------- sent news ----------
    def clear_sent_news(self, chat_id: int) -> None:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM sent_news WHERE chat_id = ?", (chat_id,))
            con.commit()

    def filter_new_items(self, chat_id: int, items: List[Dict]) -> List[Dict]:
        new_items: List[Dict] = []
        with self._connect() as con:
            cur = con.cursor()
            for item in items:
                link = (item.get("link") or "").strip()
                if not link:
                    continue

                cur.execute(
                    "INSERT OR IGNORE INTO sent_news (chat_id, link) VALUES (?, ?)",
                    (chat_id, link),
                )
                if cur.rowcount == 1:
                    new_items.append(item)
            con.commit()
        return new_items

    # ---------- chat history ----------
    def add_chat_message(self, chat_id: int, role: str, content: str) -> None:
        content = (content or "").strip()
        if not content:
            return

        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO chat_history (chat_id, role, content) VALUES (?, ?, ?)",
                (chat_id, role, content),
            )

            cur.execute(
                """
                DELETE FROM chat_history
                WHERE chat_id = ?
                  AND id NOT IN (
                    SELECT id FROM chat_history
                    WHERE chat_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                  )
                """,
                (chat_id, chat_id, CHAT_HISTORY_LIMIT),
            )

            con.commit()

    def get_chat_history(self, chat_id: int) -> List[Tuple[str, str]]:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT role, content
                FROM chat_history
                WHERE chat_id = ?
                ORDER BY id ASC
                """,
                (chat_id,),
            )
            rows = cur.fetchall()
        return [(r[0], r[1]) for r in rows]


storage = Storage(DB_PATH)
