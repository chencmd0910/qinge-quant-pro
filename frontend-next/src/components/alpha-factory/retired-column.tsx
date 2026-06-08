"use client";

import { XCircle } from "lucide-react";
import type { StrategyCard } from "./alpha-factory-layout";

interface Props {
  strategies: StrategyCard[];
  loading: boolean;
}

export default function RetiredColumn({ strategies, loading }: Props) {
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
          <div className="w-5 h-5 rounded bg-red-500/20 flex items-center justify-center">
            <XCircle size={10} className="text-red-400" />
          </div>
          <span className="text-xs font-semibold text-red-400">退役</span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            {strategies.length}
          </span>
        </div>
        <div className="text-[10px] text-slate-500">已停止交易</div>
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-3">
        {strategies.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">暂无退役策略</div>
        ) : (
          strategies.map((s) => (
            <div
              key={s.id}
              className="rounded-xl bg-slate-800/40 border border-red-500/10 hover:border-red-500/20 transition-colors p-4 opacity-75"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-400 line-through">{s.name}</span>
                    <span className="text-[9px] px-1.5 py-0.5 bg-red-500/10 text-red-400 rounded border border-red-500/20">
                      {s.version}
                    </span>
                  </div>
                  <div className="text-[10px] text-red-400 mt-0.5">Alpha失效 · {s.live_days}天</div>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-red-400" />
                  <span className="text-[10px] text-red-400">退役</span>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-2">
                <div className="p-2 rounded-lg bg-slate-700/20 text-center">
                  <div className="text-[9px] text-slate-500">夏普</div>
                  <div className="text-xs font-bold font-mono text-slate-500">{s.sharpe.toFixed(2)}</div>
                </div>
                <div className="p-2 rounded-lg bg-slate-700/20 text-center">
                  <div className="text-[9px] text-slate-500">Alpha</div>
                  <div className="text-xs font-bold font-mono text-red-400">{s.alpha}%</div>
                </div>
                <div className="p-2 rounded-lg bg-slate-700/20 text-center">
                  <div className="text-[9px] text-slate-500">最大回撤</div>
                  <div className="text-xs font-bold font-mono text-red-400">{s.max_dd}%</div>
                </div>
                <div className="p-2 rounded-lg bg-slate-700/20 text-center">
                  <div className="text-[9px] text-slate-500">年化</div>
                  <div className="text-xs font-bold font-mono text-red-400">{s.annual}%</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <div className="w-1.5 h-1.5 bg-red-400 rounded-full" />
            Alpha衰减监控自动退役
          </div>
          <span className="text-[10px] text-slate-600">归档</span>
        </div>
      </div>
    </div>
  );
}
