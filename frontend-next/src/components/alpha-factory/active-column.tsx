"use client";

import { useState } from "react";
import {
  TrendingUp, Activity, Zap, ChevronDown, ChevronUp, Pause, Play,
} from "lucide-react";
import { toast } from "@/lib/toast";
import type { StrategyCard } from "./alpha-factory-layout";

interface Props {
  strategies: StrategyCard[];
  loading: boolean;
  onRetire: (id: string) => void;
}

function StrategyCard({ strategy, onRetire }: { strategy: StrategyCard; onRetire: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  const [paused, setPaused] = useState(false);

  return (
    <div className="rounded-xl bg-slate-800/60 border border-slate-700/30 hover:border-blue-500/20 transition-colors">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">{strategy.name}</span>
              <span className="text-[9px] px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded border border-blue-500/20">
                {strategy.version}
              </span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">运行 {strategy.live_days} 天</div>
          </div>
          <div className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${paused ? "bg-amber-400" : "bg-emerald-400"}`} />
            <span className={`text-[10px] ${paused ? "text-amber-400" : "text-emerald-400"}`}>
              {paused ? "已暂停" : strategy.status}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-2">
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">夏普</div>
            <div className="text-xs font-bold font-mono">{strategy.sharpe.toFixed(1)}</div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">Alpha</div>
            <div className={`text-xs font-bold font-mono ${strategy.alpha >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {strategy.alpha >= 0 ? "+" : ""}{strategy.alpha}%
            </div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">最大回撤</div>
            <div className="text-xs font-bold font-mono text-red-400">{strategy.max_dd}%</div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">胜率</div>
            <div className="text-xs font-bold font-mono">{strategy.win_rate}%</div>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-2 p-2 rounded-lg bg-slate-700/20">
          <Activity size={10} className="text-blue-400" />
          <span className="text-[10px] text-slate-400">最近信号: {strategy.last_signal}</span>
        </div>
      </div>

      <div
        className="px-4 py-2 border-t border-slate-700/30 flex items-center justify-between cursor-pointer hover:bg-slate-800/40"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-[10px] text-slate-500">详情</span>
        {expanded ? <ChevronUp size={12} className="text-slate-500" /> : <ChevronDown size={12} className="text-slate-500" />}
      </div>

      {expanded && (
        <div className="px-4 pb-4 pt-3 border-t border-slate-700/30">
          <div className="space-y-2">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">年化收益</span>
              <span className={`font-mono ${strategy.annual >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {strategy.annual >= 0 ? "+" : ""}{strategy.annual}%
              </span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">总交易次数</span>
              <span className="font-mono">{strategy.trades}</span>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => {
                const newState = !paused;
                setPaused(newState);
                toast(newState ? "info" : "success", newState ? `${strategy.name} 已暂停` : `${strategy.name} 已恢复`);
              }}
              className={`flex-1 h-7 rounded-lg border text-[10px] font-medium transition-colors flex items-center justify-center gap-1 ${
                paused
                  ? "bg-emerald-600/20 text-emerald-400 border-emerald-500/20 hover:bg-emerald-600/30"
                  : "bg-amber-600/20 text-amber-400 border-amber-500/20 hover:bg-amber-600/30"
              }`}
            >
              {paused ? <Play size={10} /> : <Pause size={10} />}
              {paused ? "恢复" : "暂停"}
            </button>
            <button
              onClick={() => {
                toast("success", `${strategy.name} 已退役`);
                onRetire(strategy.id);
              }}
              className="flex-1 h-7 rounded-lg bg-red-600/20 text-red-400 border border-red-500/20 text-[10px] font-medium hover:bg-red-600/30 transition-colors"
            >
              退役
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ActiveColumn({ strategies, loading, onRetire }: Props) {
  const totalAlpha = strategies.reduce((sum, s) => sum + s.alpha, 0);

  if (loading) {
    return (
      <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col animate-pulse">
        <div className="h-12 bg-slate-800/50 rounded-t-xl" />
        <div className="flex-1 p-3 space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="h-40 bg-slate-800/30 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-blue-500/20 flex items-center justify-center">
            <Zap size={10} className="text-blue-400" />
          </div>
          <span className="text-xs font-semibold text-blue-400">活跃</span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            {strategies.length}
          </span>
        </div>
        <div className="text-[10px] text-emerald-400 flex items-center gap-1">
          <TrendingUp size={10} />
          总Alpha: +{totalAlpha}%
        </div>
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-3">
        {strategies.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">暂无活跃策略</div>
        ) : (
          strategies.map((s) => <StrategyCard key={s.id} strategy={s} onRetire={onRetire} />)
        )}
      </div>

      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
            所有系统运行正常
          </div>
          <span className="text-[10px] text-slate-600">运行中</span>
        </div>
      </div>
    </div>
  );
}
