"use client";

import { useEffect, useMemo, useState } from "react";
import { stripHtml } from "../lib/text";

type NewsItem = {
  id?: string;
  title: string;
  link: string;
  source?: string;
  published?: string;
  summary?: string;
  description?: string;
  topic?: string;
};

const TOPICS: { key: string; label: string }[] = [
  { key: "all", label: "Усі" },
  { key: "ukraine", label: "Україна" },
  { key: "world", label: "Світ" },
  { key: "politics", label: "Політика" },
  { key: "economy", label: "Економіка" },
  { key: "technology", label: "Технології" },
  { key: "science", label: "Наука" },
  { key: "sport", label: "Спорт" },
  { key: "business", label: "Бізнес" },
  { key: "health", label: "Здоров’я" },
  { key: "cinema", label: "Кіно" },
  { key: "games", label: "Ігри" },
];

export default function Page() {
  const [topic, setTopic] = useState<string>("all");
  const [q, setQ] = useState<string>("");
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [updatedAt, setUpdatedAt] = useState<string>("");

  async function load() {
    setLoading(true);
    setError("");

    try {
      const url = `/api/news?topic=${encodeURIComponent(topic)}&limit=30`;
      const res = await fetch(url, { cache: "no-store" });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }

      const data = await res.json();

      // очікуємо масив або { items: [...] }
      const list: NewsItem[] = Array.isArray(data) ? data : data?.items ?? [];

      setItems(list);
      setUpdatedAt(new Date().toLocaleString("uk-UA"));
    } catch (e: any) {
      setError(e?.message || "Помилка завантаження");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return items;

    return items.filter((it) => {
      const title = (it.title || "").toLowerCase();
      const rawDesc = it.summary || it.description || "";
      const desc = stripHtml(rawDesc).toLowerCase();
      return title.includes(needle) || desc.includes(needle);
    });
  }, [items, q]);

  return (
    <main style={{ maxWidth: 1200, margin: "0 auto", padding: 24 }}>
      <header style={{ marginBottom: 16 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 6 }}>Diploma News</h1>
        <div style={{ color: "#666" }}>Стрічка новин (Vercel + Next.js)</div>
      </header>

      <section
        style={{
          border: "1px solid #e5e5e5",
          borderRadius: 16,
          padding: 16,
          marginBottom: 18,
        }}
      >
        <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Стрічка новин</h2>

        <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Пошук по заголовку/опису..."
            style={{
              flex: 1,
              padding: "10px 12px",
              border: "1px solid #ddd",
              borderRadius: 10,
              outline: "none",
            }}
          />
          <button
            onClick={() => setQ("")}
            style={{
              padding: "10px 14px",
              border: "1px solid #ddd",
              borderRadius: 10,
              background: "white",
              cursor: "pointer",
            }}
          >
            Очистити
          </button>
        </div>

        <div style={{ marginBottom: 10, fontWeight: 600 }}>Теми:</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
          {TOPICS.map((t) => {
            const active = t.key === topic;
            return (
              <button
                key={t.key}
                onClick={() => setTopic(t.key)}
                style={{
                  padding: "8px 12px",
                  borderRadius: 999,
                  border: "1px solid #ddd",
                  background: active ? "#111" : "white",
                  color: active ? "white" : "#111",
                  cursor: "pointer",
                }}
              >
                {t.label}
              </button>
            );
          })}
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ color: "#666" }}>Знайдено: {filtered.length}</div>
          <div style={{ color: "#666" }}>Оновлено: {updatedAt || "-"}</div>
          <button
            onClick={load}
            disabled={loading}
            style={{
              marginLeft: "auto",
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: "white",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Завантаження..." : "Оновити"}
          </button>
        </div>

        {error ? (
          <div style={{ marginTop: 12, color: "#b00020" }}>{error}</div>
        ) : null}
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 14,
        }}
      >
        {filtered.map((it, idx) => {
          const rawDesc = it.summary || it.description || "";
          const desc = stripHtml(rawDesc);
          const source = it.source || it.topic || "";

          return (
            <article
              key={it.id || it.link || `${idx}`}
              style={{
                border: "1px solid #e5e5e5",
                borderRadius: 16,
                padding: 16,
                background: "white",
              }}
            >
              <a
                href={it.link}
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: 18, fontWeight: 700, textDecoration: "none" }}
              >
                {it.title}
              </a>

              {source ? (
                <div style={{ marginTop: 6, color: "#666", fontSize: 13 }}>{source}</div>
              ) : null}

              {desc ? (
                <div style={{ marginTop: 10, color: "#222", lineHeight: 1.45, whiteSpace: "pre-wrap" }}>
                  {desc}
                </div>
              ) : null}

              <div style={{ marginTop: 12 }}>
                <a href={it.link} target="_blank" rel="noreferrer">
                  Перейти до джерела →
                </a>
              </div>
            </article>
          );
        })}
      </section>
    </main>
  );
}
