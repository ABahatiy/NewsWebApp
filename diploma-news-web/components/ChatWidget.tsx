"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type NewsItem = {
  title: string;
  url: string;
  source: string;
  description?: string;
  published_at?: string;
};

type ChatMsg = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatWidget({ items }: { items: NewsItem[] }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      role: "assistant",
      content:
        "Привіт. Напиши питання по новинах або попроси коротко пояснити/порівняти/підсумувати.",
    },
  ]);

  const listRef = useRef<HTMLDivElement | null>(null);

  const context = useMemo(() => {
    return (items || []).slice(0, 10).map((it) => ({
      title: it.title,
      url: it.url,
      source: it.source,
      description: it.description || "",
    }));
  }, [items]);

  useEffect(() => {
    // автоскрол вниз при нових повідомленнях або лоадингу
    const el = listRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, context }),
      });

      const data = await res.json().catch(() => ({}));
      const answer = typeof data?.answer === "string" ? data.answer : "Нема відповіді.";

      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Помилка запиту до AI." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function clearChat() {
    setInput("");
    setLoading(false);
    setMessages([
      {
        role: "assistant",
        content:
          "Чат очищено. Напиши питання по новинах або попроси коротко пояснити/порівняти/підсумувати.",
      },
    ]);
  }

  // Закрита кнопка (floating)
  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-50 rounded-full border bg-white px-4 py-2 text-sm shadow-sm hover:bg-gray-50"
      >
        AI чат
      </button>
    );
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 w-[360px] max-w-[92vw]">
      <div className="rounded-2xl border bg-white shadow-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between gap-2 border-b px-4 py-3">
          <div className="font-semibold">AI чат</div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={clearChat}
              className="rounded-lg border px-2.5 py-1 text-xs hover:bg-gray-50"
            >
              Очистити
            </button>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-lg border px-2.5 py-1 text-xs hover:bg-gray-50"
            >
              Закрити
            </button>
          </div>
        </div>

        {/* Body: фіксована висота + скрол ТІЛЬКИ в списку */}
        <div className="h-[520px] max-h-[75vh] flex flex-col">
          {/* Messages (SCROLL) */}
          <div
            ref={listRef}
            className="flex-1 min-h-0 overflow-y-auto px-3 py-3 space-y-2 bg-gray-50"
          >
            {messages.map((m, idx) => {
              const isUser = m.role === "user";
              return (
                <div
                  key={idx}
                  className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={[
                      "max-w-[85%] rounded-2xl px-3 py-2 text-sm",
                      "whitespace-pre-wrap break-words",
                      isUser
                        ? "bg-gray-900 text-white"
                        : "bg-white border",
                    ].join(" ")}
                  >
                    {m.content}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl px-3 py-2 text-sm bg-white border">
                  Думаю...
                </div>
              </div>
            )}
          </div>

          {/* Input (fixed bottom) */}
          <div className="border-t bg-white p-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Напиши питання…"
              rows={2}
              className="w-full resize-none rounded-xl border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-gray-200"
              onKeyDown={(e) => {
                // Enter — send, Shift+Enter — newline
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
            />
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={send}
                disabled={loading || !input.trim()}
                className="rounded-xl bg-gray-900 px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                Відправити
              </button>
              <div className="text-xs text-gray-500 self-center">
                Enter — відправити, Shift+Enter — рядок
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
