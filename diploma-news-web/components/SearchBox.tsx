"use client";

import { useEffect, useState } from "react";

export default function SearchBox({
  value,
  onChange
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [local, setLocal] = useState(value);

  useEffect(() => setLocal(value), [value]);

  useEffect(() => {
    const t = setTimeout(() => onChange(local), 350);
    return () => clearTimeout(t);
  }, [local, onChange]);

  return (
    <div className="flex w-full items-center gap-2">
      <input
        className="input"
        placeholder="Пошук по заголовку/опису..."
        value={local}
        onChange={(e) => setLocal(e.target.value)}
      />
      <button className="btn" onClick={() => setLocal("")} type="button">
        Очистити
      </button>
    </div>
  );
}
