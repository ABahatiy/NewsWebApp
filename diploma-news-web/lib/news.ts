// diploma-news-web/lib/news.ts

export type NewsItem = {
  id: string;
  title: string;
  summary?: string | null;
  link: string;
  source?: string | null;
  publishedAt?: string | null;
  topic?: string | null;
};

export type Topic = {
  id: string;
  title: string;
  keywords?: string[];
};

const STORAGE_KEY = "topicKeywordsOverrides:v2";

export function normalizeText(s: string) {
  return (s || "")
    .toLowerCase()
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function cleanSummary(input?: string | null) {
  if (!input) return "";
  return input
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseKeywords(text: string): string[] {
  return text
    .split(/[,;\n]/g)
    .map((s) => normalizeText(s))
    .filter(Boolean);
}

/**
 * Overrides model:
 * - added: що юзер додав
 * - removed: що юзер прибрав/вимкнув із дефолтних
 */
export type TopicKeywordsOverride = {
  added?: string[];
  removed?: string[];
};

export function loadKeywordOverrides(): Record<string, TopicKeywordsOverride> {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return {};
    return parsed as Record<string, TopicKeywordsOverride>;
  } catch {
    return {};
  }
}

export function saveKeywordOverrides(map: Record<string, TopicKeywordsOverride>) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
}

export function getEffectiveKeywords(topic: Topic, ov?: TopicKeywordsOverride): string[] {
  const base = (topic.keywords ?? []).map(normalizeText).filter(Boolean);
  const added = (ov?.added ?? []).map(normalizeText).filter(Boolean);
  const removed = new Set((ov?.removed ?? []).map(normalizeText).filter(Boolean));

  // base - removed
  const filteredBase = base.filter((k) => !removed.has(k));

  // + added (без дублікатів)
  const set = new Set<string>(filteredBase);
  for (const k of added) set.add(k);

  return Array.from(set);
}

export function applyKeywordOverrides(
  topics: Topic[],
  overrides: Record<string, TopicKeywordsOverride>
): Topic[] {
  return topics.map((t) => ({
    ...t,
    keywords: getEffectiveKeywords(t, overrides[t.id]),
  }));
}

export function matchesTopic(item: NewsItem, topic?: Topic | null) {
  if (!topic || topic.id === "all") return true;

  const keywords = topic.keywords ?? [];
  if (!keywords.length) return true;

  const hay = normalizeText(
    [item.title, item.summary, item.source].filter(Boolean).join(" ")
  );

  return keywords.some((k) => hay.includes(normalizeText(k)));
}
