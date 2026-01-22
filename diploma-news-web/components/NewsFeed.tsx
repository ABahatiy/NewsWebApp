"use client";

import { useEffect, useMemo, useState } from "react";
import ChatWidget from "./ChatWidget";

type Topic = { id: string; title: string };

type NewsItem = {
  title: string;
  url: string;
  source: string;
  description?: string;
  published_at?: string;
};

type NewsApiResponse = {
  items: NewsItem[];
  meta?: { fetchedAt?: string; total?: number; topic?: string };
};

export default function NewsFeed() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [active, setActive] = useState<string>("all");
  const [q, setQ] = useState("");
  const [items, setItems] = useState<NewsItem[]>([]);
  const [fetchedAt, setFetchedAt] = useState<string>("");

  async function loadTopics() {
    const res = await fetch("/api/topics");
    const data = await res.json();
    setTopics([{ id: "all", title: "Усі" }, ...(data?.topics || [])]);
  }

  async function loadNews(topic: string) {
    const res = await fetch(`/api/news?topic=${encodeURIComponent(topic)}&limit=20`);
    const data: NewsApiResponse = await res.json();
    setItems(data?.items || []);
    setFetchedAt(data?.meta?.fetchedAt || "");
  }

  useEffect(() => {
    loadTopics();
    loadNews("all");
  }, []);

  useEffect(() => {
    loadNews(active);
  }, [active]);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return items;
    return items.filter((it) => {
      const t = (it.title || "").toLowerCase();
      const d = (it.description || "").toLowerCase();
      const src = (it.source || "").toLowerCase();
      return t.includes(s) || d.includes(s) || src.includes(s);
    });
  }, [items, q]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="rounded-2xl border bg-white p-5">
        <div className="text-2xl font-semibold">Стрічка новин</div>
        <div className="mt-1 text-sm text-gray-600">
          Дані беруться з бекенду (Render) через /api/news.
        </div>

        <div className="mt-4 flex gap-3">
          <input
            className="w-full rounded-xl border px-4 py-3 text-sm outline-none"
            placeholder="Пошук по заголовку/опису..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button
            className="rounded-xl border px-4 py-3 text-sm"
            onClick={() => setQ("")}
          >
            Очистити
          </button>
        </div>

        <div className="mt-4 text-sm font-medium">Теми:</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {topics.map((t) => {
            const on = t.id === active;
            return (
              <button
                key={t.id}
                className={`rounded-full border px-3 py-1 text-sm ${
                  on ? "bg-black text-white" : "bg-white"
                }`}
                onClick={() => setActive(t.id)}
              >
                {t.title}
              </button>
            );
          })}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-gray-700">
          <div className="rounded-full border px-3 py-1">
            Знайдено: {filtered.length}
          </div>
          <div className="rounded-full border px-3 py-1">
            Оновлено: {fetchedAt ? new Date(fetchedAt).toLocaleString() : "-"}
          </div>
          <button
            className="rounded-xl border px-4 py-2 text-sm"
            onClick={() => loadNews(active)}
          >
            Оновити
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {filtered.map((it, idx) => (
          <div key={idx} className="rounded-2xl border bg-white p-5">
            <a
              className="text-xl font-semibold text-blue-700 hover:underline"
              href={it.url}          // головне: реальний URL новини
              target="_blank"
              rel="noreferrer"
            >
              {it.title}
            </a>

            <div className="mt-2 text-sm text-gray-700">
              {it.source ? it.source : ""}
            </div>

            {it.description ? (
              <div className="mt-3 text-sm text-gray-700 line-clamp-4">
                {it.description.replace(/<[^>]+>/g, "")}
              </div>
            ) : null}

            <div className="mt-4">
              <a
                className="text-blue-700 hover:underline"
                href={it.url}
                target="_blank"
                rel="noreferrer"
              >
                Перейти до джерела →
              </a>
            </div>
          </div>
        ))}
      </div>

      <ChatWidget items={items} />
    </div>
  );
}
