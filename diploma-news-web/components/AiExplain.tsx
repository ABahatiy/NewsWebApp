"use client";

import { useState } from "react";

type Props = {
  // можна передати новини як контекст, але це опційно
  contextItems?: Array<{
    title?: string;
    url?: string;
    source?: string;
    description?: string;
  }>;
};

export default function AiExplain({ contextItems = [] }: Props) {
  const [message, setMessage] = useState("");
  const [answer, setAnswer] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const onSend = async () => {
    const text = message.trim();
    if (!text) return;

    setLoading(true);
    setError("");
    setAnswer("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          context_items: contextItems,
        }),
      });

      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setAnswer(data.answer || "");
    } catch (e: any) {
      setError(e?.message || "Помилка запиту");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-6 rounded-2xl border bg-white p-4">
      <div className="text-lg font-semibold">AI пояснення</div>
      <div className="mt-1 text-sm text-gray-600">
        Попроси коротко пояснити новину, зробити підсумок або відповісти на питання.
      </div>

      <div className="mt-3 flex gap-2">
        <input
          className="w-full rounded-xl border px-3 py-2"
          placeholder="Наприклад: Поясни коротко, про що ці новини"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSend();
          }}
        />
        <button
          className="rounded-xl border px-4 py-2"
          onClick={onSend}
          disabled={loading}
        >
          {loading ? "..." : "Надіслати"}
        </button>
      </div>

      {error ? (
        <div className="mt-3 rounded-xl border border-red-300 bg-red-50 p-3 text-sm">
          {error}
        </div>
      ) : null}

      {answer ? (
        <div className="mt-3 rounded-xl border bg-gray-50 p-3 text-sm whitespace-pre-wrap">
          {answer}
        </div>
      ) : null}
    </div>
  );
}
