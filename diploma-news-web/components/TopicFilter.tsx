"use client";

import type { Topic } from "@/lib/types";

export default function TopicFilter({
  topics,
  active,
  onChange
}: {
  topics: Topic[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {topics.map((t) => {
        const isActive = t.id === active;
        return (
          <button
            key={t.id}
            type="button"
            onClick={() => onChange(t.id)}
            className={`badge ${isActive ? "badge-active" : ""}`}
            title={
              (t.keywords ?? []).length
                ? `Ключові: ${(t.keywords ?? []).join(", ")}`
                : "Без фільтра"
            }
          >
            {t.title}
          </button>
        );
      })}
    </div>
  );
}
