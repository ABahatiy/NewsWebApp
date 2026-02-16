"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";

type Role = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: Role;
  content: string;
};

function uid() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function AIExplain() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>(() => [
    {
      id: uid(),
      role: "assistant",
      content:
        "Встав посилання на новину або текст — я коротко поясню зміст і ключові тези.",
    },
  ]);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  useEffect(() => {
    // автоскрол вниз при нових повідомленнях
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length]);

  const clearChat = () => {
    setMessages([
      {
        id: uid(),
        role: "assistant",
        content:
          "Встав посилання на новину або текст — я коротко поясню зміст і ключові тези.",
      },
    ]);
    setInput("");
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { id: uid(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // Підлаштуй endpoint під свій (якщо інший).
      // Якщо в тебе вже є /api/ai-explain або /api/ai/chat — постав його тут.
      const res = await fetch("/api/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => "");
        throw new Error(errText || `HTTP ${res.status}`);
      }

      const data = await res.json().catch(() => ({}));
      const answer =
        data?.answer ||
        data?.message ||
        data?.text ||
        "Не вдалося отримати відповідь від сервера.";

      const botMsg: ChatMessage = { id: uid(), role: "assistant", content: String(answer) };
      setMessages((prev) => [...prev, botMsg]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: "assistant",
          content: `Помилка: ${e?.message || "невідома помилка"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="w-full max-w-3xl mx-auto px-4 sm:px-6">
      {/* Контейнер чату з фіксованою висотою і без “вилазіння” */}
      <div className="w-full min-w-0 max-w-full rounded-2xl border bg-white shadow-sm overflow-hidden">
        <div className="p-4 sm:p-5 border-b">
          <h2 className="text-xl sm:text-2xl font-semibold">AI пояснення</h2>
          <p className="text-sm text-gray-600 mt-1">
            Надішли посилання або текст новини — отримаєш структурований виклад.
          </p>
        </div>

        {/* Вся область чату */}
        <div className="flex flex-col min-w-0 max-w-full h-[70vh] sm:h-[72vh]">
          {/* Прокручувана область повідомлень */}
          <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden bg-gray-50 p-3 sm:p-4">
            <div className="space-y-3 w-full min-w-0 max-w-full">
              {messages.map((m) => {
                const isUser = m.role === "user";
                return (
                  <div
                    key={m.id}
                    className={[
                      "w-full min-w-0 max-w-full flex",
                      isUser ? "justify-end" : "justify-start",
                    ].join(" ")}
                  >
                    <div
                      className={[
                        "min-w-0 max-w-[92%] sm:max-w-[85%]",
                        "rounded-2xl border px-4 py-3",
                        "bg-white",
                        isUser ? "border-blue-200" : "border-gray-200",
                      ].join(" ")}
                    >
                      <div className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap break-words overflow-x-hidden">
                        {m.content}
                      </div>
                    </div>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>
          </div>

          {/* Панель вводу (завжди знизу) */}
          <div className="border-t bg-white p-3 sm:p-4">
            <div className="flex gap-3 items-end min-w-0">
              <textarea
                className="flex-1 min-w-0 max-w-full rounded-xl border px-3 py-2 text-sm sm:text-base resize-none outline-none focus:ring-2 focus:ring-blue-200"
                rows={3}
                placeholder="Встав посилання або текст..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  // Enter = send, Shift+Enter = newline
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
              />

              <div className="flex gap-2 shrink-0">
                <button
                  type="button"
                  className="rounded-xl border px-4 py-2 text-sm sm:text-base hover:bg-gray-50"
                  onClick={clearChat}
                  disabled={loading}
                >
                  Очистити
                </button>
                <button
                  type="button"
                  className="rounded-xl bg-blue-600 text-white px-4 py-2 text-sm sm:text-base hover:bg-blue-700 disabled:opacity-60"
                  onClick={send}
                  disabled={!canSend}
                >
                  {loading ? "..." : "Відправити"}
                </button>
              </div>
            </div>

            <p className="text-xs text-gray-500 mt-2">
              Enter — відправити, Shift+Enter — новий рядок.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
