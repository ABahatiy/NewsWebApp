"use client";

import { useMemo, useState } from "react";

type Props = {
  // опціонально: якщо ти передаєш тему/текст новини — залишиться сумісним
  initialText?: string;
};

export default function AIExplain({ initialText = "" }: Props) {
  const [input, setInput] = useState(initialText);
  const [answer, setAnswer] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  async function handleSend() {
    if (!canSend) return;

    setLoading(true);
    setError("");

    try {
      // підлаштуй URL під свій реальний endpoint (у тебе вже є /api/ai або схожий)
      const res = await fetch("/api/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input }),
      });

      if (!res.ok) {
        const msg = await res.text().catch(() => "");
        throw new Error(msg || `Request failed: ${res.status}`);
      }

      const data = (await res.json()) as { answer?: string; text?: string; result?: string };
      const next =
        data.answer ??
        data.text ??
        data.result ??
        "";

      setAnswer(next || "Порожня відповідь від сервера.");
    } catch (e: any) {
      setError(e?.message || "Помилка запиту");
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setInput("");
    setAnswer("");
    setError("");
  }

  return (
    <section className="w-full">
      {/* Контейнер з фіксованою висотою. min-h-0 критично для скролу в flex */}
      <div className="mx-auto w-full max-w-3xl rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex h-[72vh] flex-col min-h-0">
          {/* Header */}
          <div className="border-b border-slate-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-slate-900">AI пояснення</h2>
            <p className="text-sm text-slate-500">
              Встав текст або посилання на новину — отримаєш коротке пояснення.
            </p>
          </div>

          {/* Body (скролиться тільки відповідь) */}
          <div className="flex flex-1 flex-col gap-4 px-6 py-4 min-h-0">
            {/* Input */}
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Встав текст/посилання на новину…"
                className="w-full resize-y bg-transparent text-slate-900 outline-none"
                rows={3}
              />

              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={!canSend}
                  className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "Відправляю…" : "Відправити"}
                </button>

                <button
                  type="button"
                  onClick={handleClear}
                  className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-100"
                >
                  Очистити
                </button>
              </div>

              {error ? (
                <p className="mt-3 text-sm text-red-600">{error}</p>
              ) : null}
            </div>

            {/* Answer box: фіксована висота + overflow */}
            <div className="flex flex-1 flex-col min-h-0">
              <div className="mb-2 text-sm font-medium text-slate-700">Відповідь</div>

              <div className="flex-1 min-h-0 rounded-xl border border-slate-200 bg-white p-4 overflow-y-auto overflow-x-hidden">
                {answer ? (
                  <div className="ai-message whitespace-pre-wrap break-words text-slate-900">
                    {answer}
                  </div>
                ) : (
                  <div className="text-sm text-slate-500">
                    Тут з’явиться відповідь після запиту.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-slate-200 px-6 py-3 text-xs text-slate-500">
            Якщо відповідь довга — прокручуй блок “Відповідь”, сторінка не буде роздуватися.
          </div>
        </div>
      </div>
    </section>
  );
}
