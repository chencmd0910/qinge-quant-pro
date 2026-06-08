"use client";

import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import api from "@/lib/axios";

interface Strategy {
  id: string;
  name: string;
  status: string;
  pnl_pct: number;
  positions: number;
}

export default function StrategySwitch() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selected, setSelected] = useState("");

  useEffect(() => {
    api.get("/api/paper-trading/strategies")
      .then(({ data }) => {
        const list = data.strategies || [];
        setStrategies(list);
        if (list.length > 0 && !selected) setSelected(list[0].id);
      })
      .catch(() => {});
  }, []);

  if (!strategies.length) return null;

  return (
    <div className="flex gap-2 flex-wrap">
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
          <span className={`text-[10px] font-mono ${s.pnl_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {s.pnl_pct >= 0 ? "+" : ""}{s.pnl_pct}%
          </span>
          <span className="text-[9px] text-slate-500">{s.positions} 仓</span>
        </button>
      ))}
    </div>
  );
}
