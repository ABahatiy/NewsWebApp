import type { NewsItem } from "@/lib/types";

function formatDate(iso?: string) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("uk-UA", { dateStyle: "medium", timeStyle: "short" });
}

export default function NewsCard({ item }: { item: NewsItem }) {
  return (
    <article className="card p-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <span className="text-xs text-zinc-600">{item.source}</span>
        <span className="text-xs text-zinc-500">{formatDate(item.publishedAt)}</span>
      </div>

      <a href={item.link} target="_blank" rel="noreferrer" className="block">
        <h3 className="text-base font-semibold leading-snug">{item.title}</h3>
      </a>

      {item.summary ? <p className="mt-2 text-sm text-zinc-700">{item.summary}</p> : null}

      <div className="mt-3">
        <a className="text-sm" href={item.link} target="_blank" rel="noreferrer">
          Перейти до джерела →
        </a>
      </div>
    </article>
  );
}
