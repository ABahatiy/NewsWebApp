export type Topic = { id: string; title: string; keywords?: string[] };

export type NewsItem = {
  id: string;
  title: string;
  link: string;        // важливо: бекенд віддає link
  source: string;
  summary?: string;    // бекенд віддає summary
  publishedAt?: string;
  topic?: string;
};
