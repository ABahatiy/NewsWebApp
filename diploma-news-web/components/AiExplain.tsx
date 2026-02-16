"use client";

import React, { useEffect, useRef } from "react";

type Message = { role: "user" | "assistant"; content: string };

type Props = {
  messages: Message[];
  input: string;
  onInputChange: (v: string) => void;
  onSend: () => void;
  onClear: () => void;
  isLoading?: boolean;
};

export default function AiExplain({
  messages,
  input,
  onInputChange,
  onSend,
  onClear,
  isLoading,
}: Props) {
  const listRef = useRef<HTMLDivElement | null>(null);

  // авто-скрол вниз після відповіді
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, isLoading]);

  return (
    <section className="w-full">
      {/* ВАЖЛИВО: min-h-0 щоб overflow працював у flex */}
      <div className="rounded-2xl border bg-white shadow-sm flex flex-col min-h-0 h-[70svh] md:h-[65vh]">
        {/* header */}
        <div className="px-4 py-3 border-b">
          <div className="font-semibold">ШІ пояснення</div>
          <div className="text-sm text-gray-500">
            Встав посилання або текст новини — отримаєш коротке пояснення.
          </div>
        </div>

        {/* messages area (СКРОЛ ТУТ) */}
        <div
          ref={listRef}
          className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-3"
        >
          {messages.length === 0 ? (
            <div className="text-sm text-gray-500">
              Напиши запит нижче, щоб почати діалог.
            </div>
          ) : (
            messages.map((m, idx) => (
              <div
                key={idx}
                className={`max-w-[900px] ${
                  m.role === "user" ? "ml-auto" : "mr-auto"
                }`}
              >
                <div
                  className={`rounded-2xl px-4 py-3 border ${
                    m.role === "user"
                      ? "bg-gray-900 text-white border-gray-900"
                      : "bg-gray-50 text-gray-900 border-gray-200"
                  }`}
                >
                  {/* ВАЖЛИВО: перенос рядків + щоб не розширювало блок */}
                  <div className="whitespace-pre-wrap break-words leading-relaxed">
                    {m.content}
                  </div>
                </div>
              </div>
            ))
          )}

          {isLoading ? (
            <div className="text-sm text-gray-500">Генерую відповідь…</div>
          ) : null}
        </div>

        {/* input area */}
        <div className="border-t p-4">
          <textarea
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            rows={3}
            className="w-full rounded-xl border px-3 py-2 outline-none focus:ring-2 focus:ring-gray-200 resize-none"
            placeholder="Встав текст/посилання та натисни «Відправити»"
          />

          <div className="mt-3 flex gap-3">
            <button
              onClick={onSend}
              disabled={!input.trim() || isLoading}
              className="rounded-xl border px-4 py-2 bg-gray-900 text-white disabled:opacity-50"
            >
              Відправити
            </button>

            <button
              onClick={onClear}
              className="rounded-xl border px-4 py-2"
              type="button"
            >
              Очистити
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
