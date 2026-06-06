"use client";

import { Circle } from "lucide-react";

const strategies = [
  {
    name: "V6F 量价_6F",
    cluster: "Volume/Price",
    annual: "+19.57%",
    sharpe: "2.500",
    alpha: "+16.9%",
    status: "ACTIVE",
  },
  {
    name: "M5F 动量_5F",
    cluster: "Momentum",
    annual: "+11.06%",
    sharpe: "1.612",
    alpha: "+10.1%",
    status: "ACTIVE",
  },
  {
    name: "F5F 基本面",
    cluster: "Fundamental",
    annual: "+15.04%",
    sharpe: "1.594",
    alpha: "+12.6%",
    status: "WATCH",
  },
  {
    name: "NF4F 北向",
    cluster: "Northbound",
    annual: "+10.50%",
    sharpe: "1.500",
    alpha: "+8.2%",
    status: "WATCH",
  },
  {
    name: "FF4F 资金流",
    cluster: "Fund Flow",
    annual: "-2.00%",
    sharpe: "1.704",
    alpha: "-2.0%",
    status: "RETIRED",
  },
];

const statusStyles: Record<string, string> = {
  ACTIVE: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  WATCH: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  RETIRED: "bg-red-500/10 text-red-400 border-red-500/20",
};

export default function StrategyMonitor() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold">策略监控</h3>
        <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
          Alpha Factory
        </span>
      </div>

      <div className="space-y-2">
        {strategies.map((s) => (
          <div
            key={s.name}
            className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
          >
            <Circle
              size={8}
              className={
                s.status === "ACTIVE"
                  ? "fill-emerald-400 text-emerald-400"
                  : s.status === "WATCH"
                  ? "fill-amber-400 text-amber-400"
                  : "fill-red-400 text-red-400"
              }
            />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium truncate">{s.name}</div>
              <div className="text-[10px] text-slate-500">{s.cluster}</div>
            </div>
            <div className="text-right">
              <div className={`text-xs font-mono font-medium ${
                s.annual.startsWith("+") ? "text-emerald-400" : "text-red-400"
              }`}>
                {s.annual}
              </div>
              <div className="text-[10px] text-slate-500 font-mono">S:{s.sharpe}</div>
            </div>
            <div className={`text-[10px] px-2 py-0.5 rounded border font-medium ${
              statusStyles[s.status]
            }`}>
              {s.status}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
