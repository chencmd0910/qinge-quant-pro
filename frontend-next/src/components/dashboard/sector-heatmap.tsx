"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface SectorItem {
  name: string;
  change: number;
  flow: number;
}

const FALLBACK_SECTORS: SectorItem[] = [
  { name: "贵金属", change: 3.25, flow: 12.8 },
  { name: "煤炭", change: 2.18, flow: 8.5 },
  { name: "银行", change: 1.52, flow: 15.3 },
  { name: "电力", change: 1.38, flow: 6.7 },
  { name: "半导体", change: -1.87, flow: -9.2 },
  { name: "消费电子", change: -2.34, flow: -11.5 },
  { name: "房地产", change: -0.92, flow: -4.8 },
  { name: "传媒", change: -1.15, flow: -5.6 },
];

export default function SectorHeatmap() {
  const [sectors, setSectors] = useState<SectorItem[]>(FALLBACK_SECTORS);

  useEffect(() => {
    fetch("http://localhost:8000/api/market/sectors")
      .then((r) => r.json())
      .then((data) => {
        if (data?.sectors) setSectors(data.sectors);
      })
      .catch(() => {});
  }, []);

  const maxAbs = Math.max(...sectors.map((s) => Math.abs(s.change)), 1);

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[11px] font-semibold">板块热力</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {sectors.map((s) => {
          const isUp = s.change >= 0;
          const barWidth = (Math.abs(s.change) / maxAbs) * 100;
          return (
            <div key={s.name} className="flex items-center gap-2 p-1.5 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.02)" }}>
              <span className="text-[10px] text-slate-400 w-14 truncate">{s.name}</span>
              <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ backgroundColor: "rgba(255,255,255,0.04)" }}>
                <div
                  className={`h-full rounded-full ${isUp ? "bg-gradient-to-r from-transparent to-red-500/60" : "bg-gradient-to-l from-transparent to-green-500/60"}`}
                  style={{
                    width: `${barWidth}%`,
                    marginLeft: isUp ? "0" : "auto",
                  }}
                />
              </div>
              <span className={`text-[10px] font-mono w-12 text-right ${isUp ? "text-red-400" : "text-green-400"}`}>
                {isUp ? "+" : ""}{s.change.toFixed(1)}%
              </span>
              <span className={`text-[9px] font-mono w-10 text-right ${s.flow >= 0 ? "text-red-300" : "text-green-300"}`}>
                {s.flow >= 0 ? "+" : ""}{s.flow.toFixed(0)}亿
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
