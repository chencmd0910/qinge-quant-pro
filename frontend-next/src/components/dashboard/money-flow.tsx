"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface FlowItem {
  label: string;
  value: number;
  status: "up" | "down" | "flat";
}

const FALLBACK: FlowItem[] = [
  { label: "主力净流入", value: 78.5, status: "up" },
  { label: "散户净流入", value: -23.2, status: "down" },
  { label: "北向资金", value: 42.1, status: "up" },
  { label: "两融余额", value: 15680, status: "flat" },
];

export default function MoneyFlow() {
  const [flows, setFlows] = useState<FlowItem[]>(FALLBACK);

  useEffect(() => {
    fetch("/api/market/overview")
      .then((r) => r.json())
      .then((data) => {
        if (data?.money_flow) setFlows(data.money_flow);
      })
      .catch(() => {});
  }, []);

  const fmt = (v: number, label: string) => {
    if (label === "两融余额") return `${(v / 10000).toFixed(0)}亿`;
    return `${v >= 0 ? "+" : ""}${v.toFixed(1)}亿`;
  };

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[11px] font-semibold">资金流向</span>
      </div>
      <div className="space-y-2">
        {flows.map((f) => (
          <div key={f.label} className="flex items-center justify-between p-2 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.02)" }}>
            <span className="text-[10px] text-slate-400">{f.label}</span>
            <div className="flex items-center gap-1.5">
              {f.status === "up" ? (
                <TrendingUp size={10} className="text-red-400" />
              ) : f.status === "down" ? (
                <TrendingDown size={10} className="text-green-400" />
              ) : null}
              <span className={`text-[10px] font-mono ${
                f.status === "up" ? "text-red-400" : f.status === "down" ? "text-green-400" : "text-slate-300"
              }`}>
                {fmt(f.value, f.label)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
