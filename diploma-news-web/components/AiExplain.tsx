"use client";

import { useMemo, useState } from "react";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

function stripHtmlEntities(s: string) {
  // прибирає типові &nbsp; та інші, щоб не засмічувало текст
  return s
    .replaceAll("&nbsp;", " ")
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", '"')
    .replaceAll("&#39;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">");
}

export default function AIExplain() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const canSend = useMemo(() => input.trim().length > 0, [input]);

  const handleClear = () => {
    setInput("");
    setMessages([]);
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    try {
      // якщо у тебе інший ендпоінт — заміни тут
      const res = await fetch("/api/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();

      const answerRaw =
        typeof data?.answer === "string"
          ? data.answer
          : typeof data?.text === "string"
          ? data.text
          : typeof data?.message === "string"
          ? data.message
          : JSON.stringify(data);

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: stripHtmlEntities(answerRaw),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Помилка: не вдалося отримати відповідь від AI.",
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }
  };

  return (
    <section className="w-full">
      {/* ВАЖЛИВО: min-w-0 + max-w-full, щоб нічого не розпирало */}
      <div className="w-full max-w-full min-w-0 rounded-2xl border bg-white p-4 sm:p-6">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-xl font-semibold leading-tight">AI Explain</h2>
            <p className="text-sm text-gray-500">
              Встав заголовок/текст новини — я коротко поясню.
            </p>
          </div>
        </div>

        {/* INPUT */}
        <div className="flex flex-col gap-3">
          <textarea
            className="w-full max-w-full min-w-0 resize-y rounded-xl border px-4 py-3 text-base outline-none focus:ring-2 focus:ring-blue-200"
            rows={3}
            placeholder="Встав текст новини або заголовок..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleSend}
              disabled={!canSend}
              className="rounded-xl border px-5 py-2 text-base disabled:cursor-not-allowed disabled:opacity-50"
            >
              Відправити
            </button>

            <button
              type="button"
              onClick={handleClear}
              className="rounded-xl border px-5 py-2 text-base"
            >
              Очистити
            </button>
          </div>
        </div>

        {/* MESSAGES */}
        <div
          className="
            mt-5
            w-full max-w-full min-w-0
            rounded-2xl border bg-gray-50
            p-3
            h-[420px] sm:h-[520px]
            overflow-y-auto
            overscroll-contain
            space-y-3
          "
        >
          {messages.map((m) => (
            <div
              key={m.id}
              className={[
                "w-full max-w-full min-w-0 rounded-2xl border p-4 bg-white",
                m.role === "user" ? "border-gray-200" : "border-gray-200",
              ].join(" ")}
            >
              <div className="min-w-0 max-w-full overflow-hidden text-base leading-relaxed whitespace-pre-wrap break-words">
                {m.content}
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
