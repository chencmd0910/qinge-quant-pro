"use client";

import { useEffect, useState } from "react";
import { Circle } from "lucide-react";
import api from "@/lib/axios";

interface StrategyItem {
  id: string;
  name: string;
  cluster: string;
  annual_return: number;
  sharpe: number;
  alpha: number;
  status: string;
  decay_status: string;
}

const statusStyles: Record<string, string> = {
  ACTIVE: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  WATCHLIST: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  RETIRED: "bg-red-500/10 text-red-400 border-red-500/20",
};

const decayLabels: Record<string, string> = {
  HEALTHY: "健康",
  DEGRADING: "衰减中",
  DEAD: "死亡",
  RECOVERING: "恢复中",
};

export default function StrategyMonitor() {
  const [strategies, setStrategies] = useState<StrategyItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/dashboard/summary")
      .then(({ data }) => {
        if (data.strategies?.length) {
          setStrategies(data.strategies);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 animate-pulse">
        <div className="h-4 w-24 bg-slate-800 rounded mb-4" />
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-12 bg-slate-800/40 rounded-lg mb-2" />
        ))}
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold">策略监控</h3>
        <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
          Alpha工厂
        </span>
      </div>

      <div className="space-y-2">
        {strategies.map((s) => (
          <div
            key={s.id}
            className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors"
          >
            <Circle
              size={8}
              className={
                s.status === "ACTIVE"
                  ? "fill-emerald-400 text-emerald-400"
                  : s.status === "WATCHLIST"
                  ? "fill-amber-400 text-amber-400"
                  : "fill-red-400 text-red-400"
              }
            />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium truncate">{s.name}</div>
              <div className="text-[10px] text-slate-500">
                {s.cluster} · {decayLabels[s.decay_status] ?? s.decay_status}
              </div>
            </div>
            <div className="text-right">
              <div className={`text-xs font-mono font-medium ${
                s.annual_return >= 0 ? "text-emerald-400" : "text-red-400"
              }`}>
                {s.annual_return >= 0 ? "+" : ""}{s.annual_return.toFixed(2)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono">α:{s.alpha.toFixed(1)}%</div>
            </div>
            <div className={`text-[10px] px-2 py-0.5 rounded border font-medium ${
              statusStyles[s.status] ?? "text-slate-400 border-slate-600"
            }`}>
              {s.status === "ACTIVE" ? "活跃" : s.status === "WATCHLIST" ? "观望" : "退役"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
