// diploma-news-web/components/NewsCard.tsx
import React from "react";

type NewsItem = {
  id: string;
  title: string;
  link: string;
  source?: string;
  summary?: string;
  publishedAt?: string;
  topic?: string;
};

function cleanHtmlText(input?: string): string {
  if (!input) return "";

  // 1) прибираємо теги
  let s = input.replace(/<[^>]*>/g, " ");

  // 2) декодуємо найчастіші HTML-ентіті (без залежностей)
  s = s
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");

  // 3) прибираємо зайві пробіли/переноси
  s = s.replace(/\s+/g, " ").trim();

  return s;
}

export default function NewsCard({ item }: { item: NewsItem }) {
  const subtitle = cleanHtmlText(item.summary);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-xl font-semibold leading-snug text-blue-700">
        {item.title} href={item.link}
      </h3>

      <div className="mt-2 text-sm text-slate-500">
        {item.topic ? <span>{item.topic}</span> : null}
        {item.source ? (
          <>
            {item.topic ? <span> · </span> : null}
            <span>{item.source}</span>
          </>
        ) : null}
      </div>

      {subtitle ? (
        <p className="mt-4 text-base leading-relaxed text-slate-700">
          {subtitle}
        </p>
      ) : null}

      {item.link ? (
        <a
          className="mt-5 inline-flex items-center gap-2 text-blue-700 hover:underline"
          href={item.link}
          target="_blank"
          rel="noopener noreferrer"
        >
          Перейти до джерела →
        </a>
      ) : null}
    </div>
  );
}
