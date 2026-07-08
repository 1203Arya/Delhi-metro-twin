"use client";

import { useState, useRef, useMemo, useEffect } from "react";
import type { StationList } from "@/types/api";

interface StationSearchProps {
  stations: StationList[];
  selectedCode: string | null;
  onSelect: (station: StationList) => void;
}

export function StationSearch({ stations, selectedCode, onSelect }: StationSearchProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selectedName = useMemo(() => {
    if (!selectedCode) return "";
    const s = stations.find((st) => st.code === selectedCode);
    return s ? `${s.code} — ${s.name}` : "";
  }, [stations, selectedCode]);

  const filtered = useMemo(() => {
    if (!query.trim()) return stations;
    const q = query.toLowerCase();
    return stations.filter(
      (s) =>
        s.code.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q),
    );
  }, [stations, query]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={ref} className="relative w-56">
      <input
        ref={inputRef}
        type="text"
        placeholder="Visit a station..."
        className="input h-7 text-xs"
        value={open ? query : selectedName || query}
        onChange={(e) => {
          setQuery(e.target.value);
          if (!open) setOpen(true);
        }}
        onFocus={() => setOpen(true)}
      />
      {open && (
        <div className="absolute left-0 top-full z-30 mt-1 max-h-60 w-full overflow-y-auto rounded-md border border-surface-300 bg-white shadow-lg dark:border-surface-600 dark:bg-surface-800">
          {filtered.length === 0 ? (
            <div className="px-3 py-2 text-xs text-surface-400">
              No stations match &quot;{query}&quot;
            </div>
          ) : (
            filtered.map((s) => (
              <button
                key={s.id}
                className={`flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs hover:bg-surface-100 dark:hover:bg-surface-700 ${
                  s.code === selectedCode
                    ? "bg-blue-50 font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                    : "text-surface-700 dark:text-surface-300"
                }`}
                onClick={() => {
                  onSelect(s);
                  setQuery("");
                  setOpen(false);
                  inputRef.current?.blur();
                }}
              >
                <span className="font-mono">{s.code}</span>
                <span className="truncate text-surface-500">{s.name}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
