"use client";

import type { ReactNode } from "react";

interface AIPredictionCardProps {
  title: string;
  icon: string;
  children: ReactNode;
}

export function AIPredictionCard({ title, icon, children }: AIPredictionCardProps) {
  return (
    <div className="card">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-lg">{icon}</span>
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      {children}
    </div>
  );
}

export function MetricRow({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-surface-50 px-3 py-2 dark:bg-surface-800">
      <span className="text-xs text-surface-500">{label}</span>
      <span className="text-sm font-bold">
        {value}
        {unit && <span className="ml-1 text-xs font-normal text-surface-400">{unit}</span>}
      </span>
    </div>
  );
}
