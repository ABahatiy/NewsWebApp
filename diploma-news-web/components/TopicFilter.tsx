// diploma-news-web/components/TopicFilter.tsx
"use client";

import { useEffect, useMemo, useState } from "react";
import type { Topic, TopicKeywordsOverride } from "../lib/news";
import {
  applyKeywordOverrides,
  getEffectiveKeywords,
  loadKeywordOverrides,
  normalizeText,
  parseKeywords,
  saveKeywordOverrides,
} from "../lib/news";

type Props = {
  topics: Topic[];
  activeTopicId: string;
  onChange: (topicId: string) => void;
};

export default function TopicFilter({ topics, activeTopicId, onChange }: Props) {
  const [overrides, setOverrides] = useState<Record<string, TopicKeywordsOverride>>({});
  const [isEditing, setIsEditing] = useState(false);

  // Draft state (тільки для активної теми)
  const [draftAdded, setDraftAdded] = useState("");
  const [draftRemoved, setDraftRemoved] = useState<Record<string, boolean>>({}); // keyword -> removed?

  useEffect(() => {
    setOverrides(loadKeywordOverrides());
  }, []);

  const activeBaseTopic = useMemo(() => {
    return topics.find((t) => t.id === activeTopicId) || null;
  }, [topics, activeTopicId]);

  const activeOverride = useMemo(() => {
    return overrides[activeTopicId] || {};
  }, [overrides, activeTopicId]);

  const topicsWithOverrides = useMemo(() => {
    return applyKeywordOverrides(topics, overrides);
  }, [topics, overrides]);

  const activeEffectiveTopic = useMemo(() => {
    return topicsWithOverrides.find((t) => t.id === activeTopicId) || null;
  }, [topicsWithOverrides, activeTopicId]);

  // при зміні теми — ініціалізуємо draft
  useEffect(() => {
    if (!activeBaseTopic) return;

    setIsEditing(false);

    const base = (activeBaseTopic.keywords ?? []).map(normalizeText).filter(Boolean);
    const removedSet = new Set((activeOverride.removed ?? []).map(normalizeText));
    const removedMap: Record<string, boolean> = {};
    for (const k of base) removedMap[k] = removedSet.has(k);

    setDraftRemoved(removedMap);
    setDraftAdded((activeOverride.added ?? []).join(", "));
  }, [activeTopicId]); // важливо тільки по id

  const baseKeywords = useMemo(() => {
    return (activeBaseTopic?.keywords ?? []).map(normalizeText).filter(Boolean);
  }, [activeBaseTopic]);

  const effectiveKeywordsPreview = useMemo(() => {
    if (!activeBaseTopic) return [];
    const ov: TopicKeywordsOverride = {
      added: parseKeywords(draftAdded),
      removed: Object.entries(draftRemoved)
        .filter(([, v]) => v)
        .map(([k]) => k),
    };
    return getEffectiveKeywords(activeBaseTopic, ov);
  }, [activeBaseTopic, draftAdded, draftRemoved]);

  const handleSave = () => {
    if (!activeBaseTopic) return;
    if (activeBaseTopic.id === "all") return;

    const next = { ...overrides };
    next[activeBaseTopic.id] = {
      added: parseKeywords(draftAdded),
      removed: Object.entries(draftRemoved)
        .filter(([, v]) => v)
        .map(([k]) => k),
    };

    setOverrides(next);
    saveKeywordOverrides(next);
    setIsEditing(false);
  };

  const handleResetAll = () => {
    if (!activeBaseTopic) return;
    if (activeBaseTopic.id === "all") return;

    const next = { ...overrides };
    delete next[activeBaseTopic.id];
    setOverrides(next);
    saveKeywordOverrides(next);

    // скидаємо draft
    const removedMap: Record<string, boolean> = {};
    for (const k of baseKeywords) removedMap[k] = false;
    setDraftRemoved(removedMap);
    setDraftAdded("");
    setIsEditing(false);
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {topicsWithOverrides.map((t) => {
          const isActive = t.id === activeTopicId;
          const kw = t.keywords ?? [];
          return (
            <button
              key={t.id}
              onClick={() => onChange(t.id)}
              className={`badge ${isActive ? "badge-active" : ""}`}
              title={kw.length ? `Ключові: ${kw.join(", ")}` : "Без ключових слів"}
              type="button"
            >
              {t.title}
            </button>
          );
        })}
      </div>

      {activeBaseTopic && activeBaseTopic.id !== "all" && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm font-medium text-slate-900">
              Ключові слова: <span className="font-semibold">{activeBaseTopic.title}</span>
            </div>

            {!isEditing ? (
              <button type="button" className="btn" onClick={() => setIsEditing(true)}>
                Редагувати
              </button>
            ) : (
              <div className="flex gap-2">
                <button type="button" className="btn" onClick={handleSave}>
                  Зберегти
                </button>
                <button type="button" className="btn" onClick={() => setIsEditing(false)}>
                  Скасувати
                </button>
              </div>
            )}
          </div>

          {/* VIEW */}
          {!isEditing ? (
            <div className="mt-3 text-sm text-slate-700">
              {(activeEffectiveTopic?.keywords ?? []).length
                ? (activeEffectiveTopic?.keywords ?? []).join(", ")
                : "Немає ключових слів."}
              {!!(overrides[activeTopicId]?.added?.length || overrides[activeTopicId]?.removed?.length) && (
                <div className="mt-2 text-xs text-slate-500">
                  Є твої зміни (додані/вимкнені слова) — зберігаються у браузері.
                </div>
              )}
            </div>
          ) : (
            <>
              {/* EDIT дефолтних */}
              <div className="mt-3">
                <div className="text-xs font-medium text-slate-600 mb-2">
                  Дефолтні ключові (можна вимкнути):
                </div>

                <div className="flex flex-wrap gap-2">
                  {baseKeywords.length ? (
                    baseKeywords.map((k) => {
                      const removed = !!draftRemoved[k];
                      return (
                        <button
                          key={k}
                          type="button"
                          className={`badge ${removed ? "opacity-50 line-through" : ""}`}
                          onClick={() =>
                            setDraftRemoved((prev) => ({ ...prev, [k]: !prev[k] }))
                          }
                          title={removed ? "Натисни, щоб повернути" : "Натисни, щоб вимкнути"}
                        >
                          {k}
                        </button>
                      );
                    })
                  ) : (
                    <div className="text-sm text-slate-500">Немає дефолтних ключових.</div>
                  )}
                </div>
              </div>

              {/* EDIT додаткових */}
              <div className="mt-4">
                <div className="text-xs font-medium text-slate-600 mb-2">
                  Додати свої ключові:
                </div>
                <textarea
                  value={draftAdded}
                  onChange={(e) => setDraftAdded(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 p-3 text-sm outline-none focus:border-slate-400"
                  rows={3}
                  placeholder="Введи слова через кому, ; або з нового рядка"
                />
                <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-xs text-slate-500">
                    Розділювачі: кома, ;, новий рядок
                  </div>
                  <button type="button" className="btn" onClick={handleResetAll}>
                    Скинути мої зміни
                  </button>
                </div>
              </div>

              {/* PREVIEW */}
              <div className="mt-4 rounded-lg bg-slate-50 p-3">
                <div className="text-xs font-medium text-slate-600 mb-1">
                  Після збереження буде:
                </div>
                <div className="text-sm text-slate-700">
                  {effectiveKeywordsPreview.length
                    ? effectiveKeywordsPreview.join(", ")
                    : "Немає ключових слів."}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
