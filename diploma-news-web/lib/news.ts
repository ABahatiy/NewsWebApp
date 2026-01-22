import Parser from "rss-parser";
import { DEFAULT_LIMIT, RSS_SOURCES, TOPICS } from "@/lib/config";
import type { NewsItem, Topic } from "@/lib/types";

type RssItem = {
  title?: string;
  link?: string;
  pubDate?: string;
  contentSnippet?: string;
  content?: string;
  guid?: string;
  isoDate?: string;
};

const parser = new Parser();

function safeText(v?: string) {
  return (v ?? "").trim();
}

function normalizeText(v: string) {
  return v.toLowerCase();
}

function pickSummary(item: RssItem) {
  const s = item.contentSnippet || item.content || "";
  return safeText(s).replace(/\s+/g, " ").slice(0, 220);
}

function toId(sourceId: string, item: RssItem) {
  const base = item.guid || item.link || item.title || `${Math.random()}`;
  return `${sourceId}:${base}`.slice(0, 220);
}

function matchesTopic(item: NewsItem, topic: Topic) {
  if (!topic || topic.id === "all") return true;
  const hay = normalizeText([item.title, item.summary, item.source].filter(Boolean).join(" "));
  return topic.keywords.some((k) => hay.includes(normalizeText(k)));
}

function matchesQuery(item: NewsItem, q?: string) {
  const query = safeText(q);
  if (!query) return true;
  const hay = normalizeText([item.title, item.summary, item.source].filter(Boolean).join(" "));
  return hay.includes(normalizeText(query));
}

export async function fetchNews(params: {
  q?: string;
  topic?: string;
  limit?: number;
}): Promise<{ items: NewsItem[]; topics: Topic[] }> {
  const topicId = safeText(params.topic) || "all";
  const topicObj = TOPICS.find((t) => t.id === topicId) ?? TOPICS[0];
  const limit = Math.max(1, Math.min(params.limit ?? DEFAULT_LIMIT, 100));

  const feeds = await Promise.all(
    RSS_SOURCES.map(async (src) => {
      try {
        const feed = await parser.parseURL(src.url);
        const items = (feed.items ?? []) as RssItem[];

        const mapped: NewsItem[] = items
          .map((it) => {
            const title = safeText(it.title);
            const link = safeText(it.link);
            if (!title || !link) return null;

            return {
              id: toId(src.id, it),
              title,
              link,
              source: src.title,
              publishedAt: it.isoDate || it.pubDate,
              summary: pickSummary(it)
            } satisfies NewsItem;
          })
          .filter(Boolean) as NewsItem[];

        return mapped;
      } catch {
        return [];
      }
    })
  );

  const all = feeds.flat();

  // Фільтри
  const filtered = all
    .filter((it) => matchesTopic(it, topicObj))
    .filter((it) => matchesQuery(it, params.q));

  // Сортування за датою (якщо є), інакше — як є
  filtered.sort((a, b) => {
    const da = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
    const db = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
    return db - da;
  });

  return {
    items: filtered.slice(0, limit),
    topics: TOPICS
  };
}
