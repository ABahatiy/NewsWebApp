"use client";

import { useEffect, useMemo, useState } from "react";
import NewsCard from "./NewsCard";
import ChatWidget from "./ChatWidget";
import type { NewsItem, Topic } from "@/lib/types";

type NewsApiResponse = {
  items: NewsItem[];
  topics?: Topic[];
  meta?: { fetchedAt?: string; total?: number; topic?: string };
};

export default function NewsFeed() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [active, setActive] = useState("all");
  const [q, setQ] = useState("");
  const [items, setItems] = useState<NewsItem[]>([]);
  const [fetchedAt, setFetchedAt] = useState("");

  async function loadTopics() {
    const res = await fetch("/api/topics", { cache: "no-store" });
    const data: NewsApiResponse = await res.json();
    setTopics([{ id: "all", title: "Усі" }, ...(data?.topics || [])]);
  }

  async function loadNews(topic: string) {
    const res = await fetch(
      `/api/news?topic=${encodeURIComponent(topic)}&limit=20`,
      { cache: "no-store" }
    );
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
      const sum = (it.summary || "").toLowerCase();
      const src = (it.source || "").toLowerCase();
      return t.includes(s) || sum.includes(s) || src.includes(s);
    });
  }, [items, q]);

  return (
    <main className="mx-auto max-w-6xl px-4 py-10">
      <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-3xl font-bold">Стрічка новин</h1>

        <div className="mt-5 flex flex-col gap-3 md:flex-row md:items-center">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Пошук по заголовку/опису..."
            className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:ring-2 focus:ring-slate-200"
          />
          <button
            onClick={() => setQ("")}
            className="rounded-xl border border-slate-200 px-5 py-3"
          >
            Очистити
          </button>
        </div>

        <div className="mt-5">
          <div className="mb-2 font-medium">Теми:</div>
          <div className="flex flex-wrap gap-2">
            {topics.map((t) => {
              const on = t.id === active;
              return (
                <button
                  key={t.id}
                  onClick={() => setActive(t.id)}
                  className={[
                    "rounded-full border px-4 py-2 text-sm",
                    on
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-200 bg-white",
                  ].join(" ")}
                >
                  {t.title}
                </button>
              );
            })}
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-600">
            <span className="rounded-full border border-slate-200 px-3 py-1">
              Знайдено: {filtered.length}
            </span>
            <span className="rounded-full border border-slate-200 px-3 py-1">
              Оновлено:{" "}
              {fetchedAt ? new Date(fetchedAt).toLocaleString() : "-"}
            </span>
            <button
              onClick={() => loadNews(active)}
              className="rounded-xl border border-slate-200 px-4 py-2 text-slate-900"
            >
              Оновити
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {filtered.map((it) => (
          <NewsCard key={it.id || `${it.source}-${it.title}`} item={it} />
        ))}
      </div>

      <ChatWidget items={[]} />
    </main>
  );
}
