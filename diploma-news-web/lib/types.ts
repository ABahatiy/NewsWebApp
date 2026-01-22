export type NewsItem = {
  id: string;
  title: string;
  link: string;
  source: string;
  publishedAt?: string; // ISO
  summary?: string;
  topic?: string;
};

export type Topic = {
  id: string;
  title: string;
  keywords: string[];
};

export type NewsApiResponse = {
  items: NewsItem[];
  topics: Topic[];
  meta: {
    fetchedAt: string; // ISO
    total: number;
    query?: string;
    topic?: string;
  };
};
