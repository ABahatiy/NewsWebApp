"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { NewsApiResponse, NewsItem, Topic } from "@/lib/types";
import SearchBox from "@/components/SearchBox";
import TopicFilter from "@/components/TopicFilter";
import NewsCard from "@/components/NewsCard";

export default function NewsFeed() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [topics, setTopics] = useState<Topic[]>([{ id: "all", title: "Усі", keywords: [] }]);
  const [activeTopic, setActiveTopic] = useState<string>("all");
  const [query, setQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [meta, setMeta] = useState<{ fetchedAt?: string; total?: number }>({});

  const apiUrl = useMemo(() => {
    const sp = new URLSearchParams();
    if (query.trim()) sp.set("q", query.trim());
    if (activeTopic && activeTopic !== "all") sp.set("topic", activeTopic);
    sp.set("limit", "30");
    return `/api/news?${sp.toString()}`;
  }, [query, activeTopic]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl, { cache: "no-store" });
      const data = (await res.json()) as NewsApiResponse;

      setItems(data.items ?? []);
      setTopics(data.topics ?? [{ id: "all", title: "Усі", keywords: [] }]);
      setMeta({ fetchedAt: data.meta?.fetchedAt, total: data.meta?.total });
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="flex flex-col gap-5">
      <section className="card p-4">
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-2">
            <h1 className="text-xl font-semibold">Стрічка новин</h1>
            <p className="text-sm text-zinc-600">
              Фільтруй по темах і пошуку. Дані беруться з RSS і віддаються через <code>/api/news</code>.
            </p>
          </div>

          <SearchBox value={query} onChange={setQuery} />

          <div className="flex flex-col gap-2">
            <div className="text-sm font-medium text-zinc-800">Теми:</div>
            <TopicFilter topics={topics} active={activeTopic} onChange={setActiveTopic} />
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-600">
            <span className="badge">Знайдено: {meta.total ?? 0}</span>
            {meta.fetchedAt ? <span className="badge">Оновлено: {new Date(meta.fetchedAt).toLocaleString("uk-UA")}</span> : null}
            <button className="btn" type="button" onClick={() => void load()}>
              Оновити
            </button>
          </div>
        </div>
      </section>

      {loading ? (
        <div className="card p-6 text-sm text-zinc-600">Завантаження новин…</div>
      ) : items.length === 0 ? (
        <div className="card p-6 text-sm text-zinc-600">
          Нічого не знайдено. Спробуй змінити тему або запит.
        </div>
      ) : (
        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {items.map((it) => (
            <NewsCard key={it.id} item={it} />
          ))}
        </section>
      )}
    </div>
  );
}
