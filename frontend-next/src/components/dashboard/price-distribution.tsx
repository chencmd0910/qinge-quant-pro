"use client";

import { useEffect, useState } from "react";

interface DistItem {
  label: string;
  count: number;
  color: string;
}

const FALLBACK_DIST: DistItem[] = [
  { label: "跌停", count: 8, color: "#2563eb" },
  { label: "-5%以下", count: 156, color: "#3b82f6" },
  { label: "-5%~-2%", count: 486, color: "#60a5fa" },
  { label: "-2%~0%", count: 892, color: "#93c5fd" },
  { label: "0%~2%", count: 1234, color: "#fbbf24" },
  { label: "2%~5%", count: 456, color: "#f59e0b" },
  { label: "5%以上", count: 128, color: "#ef4444" },
  { label: "涨停", count: 45, color: "#dc2626" },
];

export default function PriceDistribution() {
  const [dist, setDist] = useState<DistItem[]>(FALLBACK_DIST);
  const maxCount = Math.max(...dist.map((d) => d.count));

  useEffect(() => {
    // TODO: 接入真实数据
  }, []);

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[11px] font-semibold">涨跌分布</span>
      </div>
      <div className="flex items-end gap-1.5 h-24">
        {dist.map((d) => (
          <div key={d.label} className="flex-1 flex flex-col items-center gap-1">
            <span className="text-[9px] text-slate-500">{d.count}</span>
            <div
              className="w-full rounded-t-sm transition-all"
              style={{
                height: `${(d.count / maxCount) * 100}%`,
                backgroundColor: d.color,
                minHeight: "4px",
              }}
            />
            <span className="text-[8px] text-slate-500 text-center leading-tight">{d.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
