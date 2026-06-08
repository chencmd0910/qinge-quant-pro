"use client";

import { Eye } from "lucide-react";
import { toast } from "@/lib/toast";
import type { StrategyCard } from "./alpha-factory-layout";

interface Props {
  strategies: StrategyCard[];
  loading: boolean;
  onPromote: (id: string) => void;
  onRetire: (id: string) => void;
}

const decayLabels: Record<string, { label: string; color: string }> = {
  HEALTHY: { label: "健康", color: "text-emerald-400" },
  DEGRADING: { label: "衰减中", color: "text-amber-400" },
  DEAD: { label: "死亡", color: "text-red-400" },
  RECOVERING: { label: "恢复中", color: "text-blue-400" },
};

export default function WatchlistColumn({ strategies, loading, onPromote, onRetire }: Props) {
  const avgSharpe = strategies.length > 0
    ? strategies.reduce((s, x) => s + x.sharpe, 0) / strategies.length
    : 0;

  if (loading) {
    return (
      <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col animate-pulse">
        <div className="h-12 bg-slate-800/50 rounded-t-xl" />
        <div className="flex-1 p-3 space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-28 bg-slate-800/30 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-amber-500/20 flex items-center justify-center">
            <Eye size={10} className="text-amber-400" />
          </div>
          <span className="text-xs font-semibold text-amber-400">观察</span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            {strategies.length}
          </span>
        </div>
        <div className="text-[10px] text-amber-400 flex items-center gap-1">
          平均夏普: {avgSharpe.toFixed(2)}
        </div>
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-3">
        {strategies.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">暂无观察策略</div>
        ) : (
          strategies.map((s) => {
            const decay = decayLabels[s.decay_status] ?? { label: s.decay_status, color: "text-slate-400" };
            return (
              <div
                key={s.id}
                className="rounded-xl bg-slate-800/60 border border-amber-500/10 hover:border-amber-500/20 transition-colors p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{s.name}</span>
                      <span className="text-[9px] px-1.5 py-0.5 bg-amber-500/10 text-amber-400 rounded border border-amber-500/20">
                        {s.version}
                      </span>
                    </div>
                    <div className={`text-[10px] ${decay.color} mt-0.5`}>{decay.label}</div>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-amber-400" />
                    <span className="text-[10px] text-amber-400">观察</span>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-2">
                  <div className="p-2 rounded-lg bg-slate-700/30 text-center">
                    <div className="text-[9px] text-slate-500">夏普</div>
                    <div className="text-xs font-bold font-mono">{s.sharpe.toFixed(2)}</div>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-700/30 text-center">
                    <div className="text-[9px] text-slate-500">Alpha</div>
                    <div className={`text-xs font-bold font-mono ${s.alpha >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {s.alpha >= 0 ? "+" : ""}{s.alpha}%
                    </div>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-700/30 text-center">
                    <div className="text-[9px] text-slate-500">最大回撤</div>
                    <div className="text-xs font-bold font-mono text-red-400">{s.max_dd}%</div>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-700/30 text-center">
                    <div className="text-[9px] text-slate-500">年化</div>
                    <div className={`text-xs font-bold font-mono ${s.annual >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {s.annual >= 0 ? "+" : ""}{s.annual}%
                    </div>
                  </div>
                </div>

                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => {
                      toast("success", `${s.name} 已晋升到活跃`);
                      onPromote(s.id);
                    }}
                    className="flex-1 h-6 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[10px] font-medium hover:bg-emerald-600/30 transition-colors"
                  >
                    晋升
                  </button>
                  <button
                    onClick={() => {
                      toast("info", `${s.name} 已退役`);
                      onRetire(s.id);
                    }}
                    className="flex-1 h-6 rounded-lg bg-red-600/20 text-red-400 border border-red-500/20 text-[10px] font-medium hover:bg-red-600/30 transition-colors"
                  >
                    退役
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
