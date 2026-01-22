"use client";

import { useMemo, useState } from "react";

type NewsItem = {
  title: string;
  url: string;
  source: string;
  description?: string;
  published_at?: string;
};

export default function ChatWidget({ items }: { items: NewsItem[] }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const context = useMemo(() => {
    // даємо агенту короткий контекст (до 10 новин)
    return (items || []).slice(0, 10).map((it) => ({
      title: it.title,
      url: it.url,
      source: it.source,
      description: it.description || "",
    }));
  }, [items]);

  async function send() {
    const text = message.trim();
    if (!text) return;

    setLoading(true);
    setAnswer("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, context }),
      });

      const data = await res.json();
      setAnswer(data?.answer || "Нема відповіді.");
    } catch {
      setAnswer("Помилка запиту до AI.");
    } finally {
      setLoading(false);
    }
  }

  if (!open) {
    return (
      <button
        className="fixed bottom-6 right-6 rounded-xl border bg-white px-4 py-2 shadow-sm"
        onClick={() => setOpen(true)}
      >
        AI
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-[360px] max-w-[90vw] rounded-2xl border bg-white shadow-sm">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="font-medium">AI агент</div>
        <button className="text-sm text-gray-600" onClick={() => setOpen(false)}>
          Закрити
        </button>
      </div>

      <div className="px-4 py-3">
        <div className="text-sm text-gray-600">
          Питай про новини, підсумуй, порівняй, поясни.
        </div>

        <textarea
          className="mt-3 w-full rounded-xl border p-3 text-sm outline-none"
          rows={3}
          placeholder="Напиши запит..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />

        <div className="mt-2 flex gap-2">
          <button
            className="rounded-xl border px-4 py-2 text-sm"
            onClick={send}
            disabled={loading}
          >
            {loading ? "..." : "Відправити"}
          </button>
          <button
            className="rounded-xl border px-4 py-2 text-sm"
            onClick={() => {
              setMessage("");
              setAnswer("");
            }}
          >
            Очистити
          </button>
        </div>

        {answer && (
          <div className="mt-3 rounded-xl border bg-gray-50 p-3 text-sm whitespace-pre-wrap">
            {answer}
          </div>
        )}
      </div>
    </div>
  );
}
