import type { NewsItem } from "@/lib/types";

function formatDate(iso?: string) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("uk-UA", { dateStyle: "medium", timeStyle: "short" });
}

function stripHtml(s?: string) {
  if (!s) return "";
  return s.replace(/<[^>]+>/g, "").trim();
}

export default function NewsCard({ item }: { item: NewsItem }) {
  const href = (item.link || "").trim();

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-3 text-sm text-slate-500">
        <span>{item.source || ""}</span>
        {item.publishedAt ? (
          <>
            <span className="mx-2">•</span>
            <span>{formatDate(item.publishedAt)}</span>
          </>
        ) : null}
      </div>

      <div className="text-xl font-semibold leading-snug text-blue-700">
        {href ? (
          <a href={href} target="_blank" rel="noreferrer">
            {item.title}
          </a>
        ) : (
          <span>{item.title}</span>
        )}
      </div>

      {item.summary ? (
        <p className="mt-3 text-slate-700">{stripHtml(item.summary)}</p>
      ) : null}

      {href ? (
        <div className="mt-4">
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-blue-700 hover:underline"
          >
            Перейти до джерела →
          </a>
        </div>
      ) : null}
    </div>
  );
}
