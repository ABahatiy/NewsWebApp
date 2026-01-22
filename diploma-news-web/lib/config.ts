import type { Topic } from "@/lib/types";

export const RSS_SOURCES: { id: string; title: string; url: string }[] = [
  {
    id: "bbc_world",
    title: "BBC World",
    url: "https://feeds.bbci.co.uk/news/world/rss.xml"
  },
  {
    id: "reuters_top",
    title: "Reuters (top news)",
    url: "https://feeds.reuters.com/reuters/topNews"
  },
  {
    id: "theverge",
    title: "The Verge",
    url: "https://www.theverge.com/rss/index.xml"
  }
];

export const TOPICS: Topic[] = [
  {
    id: "all",
    title: "Усі",
    keywords: []
  },
  {
    id: "ai",
    title: "ШІ",
    keywords: ["ai", "artificial intelligence", "openai", "chatgpt", "llm", "нейромереж", "штучн"]
  },
  {
    id: "tech",
    title: "Технології",
    keywords: ["tech", "software", "startup", "mobile", "cloud", "security", "кібер", "технолог"]
  },
  {
    id: "world",
    title: "Світ",
    keywords: ["world", "global", "europe", "ukraine", "war", "санкц", "світ", "європ", "україн"]
  }
];

// Обмеження на кількість карток у стрічці (можна змінювати)
export const DEFAULT_LIMIT = 30;
