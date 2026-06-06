"use client";

import { useState } from "react";
import { Activity, Play, Pause } from "lucide-react";

const strategies = [
  { id: "etf-v6f", name: "ETF Rotation V6F", status: "running", pnl: "+8.2%", positions: 1 },
  { id: "mf-v25", name: "Multi-Factor V25", status: "running", pnl: "+4.1%", positions: 5 },
  { id: "nb-alpha", name: "Northbound Alpha", status: "paused", pnl: "+0.8%", positions: 0 },
];

export default function StrategySwitch() {
  const [selected, setSelected] = useState("etf-v6f");

  return (
    <div className="flex gap-2">
      {strategies.map((s) => (
        <button
          key={s.id}
          onClick={() => setSelected(s.id)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
            selected === s.id
              ? "bg-slate-800 border-blue-500/30"
              : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className={`w-2 h-2 rounded-full ${s.status === "running" ? "bg-emerald-400" : "bg-amber-400"}`} />
          <span className="text-xs font-medium">{s.name}</span>
          <span className={`text-[10px] font-mono ${s.pnl.startsWith("+") ? "text-emerald-400" : "text-red-400"}`}>
            {s.pnl}
          </span>
          <span className="text-[9px] text-slate-500">{s.positions} pos</span>
        </button>
      ))}
    </div>
  );
}
