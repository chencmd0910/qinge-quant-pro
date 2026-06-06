"use client";

import { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Play,
  Pause,
  MoreHorizontal,
  Activity,
  Shield,
  Zap,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface StrategyCard {
  id: string;
  name: string;
  version: string;
  sharpe: number;
  alpha: number;
  maxDD: number;
  annual: number;
  liveDays: number;
  winRate: number;
  trades: number;
  lastSignal: string;
  status: "ACTIVE" | "DEGRADED";
}

const activeStrategies: StrategyCard[] = [
  {
    id: "etf-v6f",
    name: "ETF Rotation V6F",
    version: "V6F",
    sharpe: 2.5,
    alpha: 16.9,
    maxDD: -5.0,
    annual: 19.57,
    liveDays: 127,
    winRate: 100,
    trades: 108,
    lastSignal: "买入 159915.SZ",
    status: "ACTIVE",
  },
  {
    id: "mf-v25",
    name: "Multi-Factor V25",
    version: "V25",
    sharpe: 2.1,
    alpha: 12.5,
    maxDD: -18.5,
    annual: 15.04,
    liveDays: 89,
    winRate: 58,
    trades: 240,
    lastSignal: "持有 600519.SH",
    status: "ACTIVE",
  },
];

function StrategyCard({ strategy }: { strategy: StrategyCard }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl bg-slate-800/60 border border-slate-700/30 hover:border-blue-500/20 transition-colors">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">{strategy.name}</span>
              <span className="text-[9px] px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded border border-blue-500/20">
                {strategy.version}
              </span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Live {strategy.liveDays} days</div>
          </div>
          <div className="flex items-center gap-1">
            <div className={`w-2 h-2 rounded-full ${strategy.status === "ACTIVE" ? "bg-emerald-400" : "bg-amber-400"}`} />
            <span className={`text-[10px] ${strategy.status === "ACTIVE" ? "text-emerald-400" : "text-amber-400"}`}>
              {strategy.status}
            </span>
          </div>
        </div>

        {/* Metrics grid */}
        <div className="grid grid-cols-4 gap-2">
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">Sharpe</div>
            <div className="text-xs font-bold font-mono">{strategy.sharpe.toFixed(1)}</div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">Alpha</div>
            <div className="text-xs font-bold font-mono text-emerald-400">+{strategy.alpha}%</div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">MaxDD</div>
            <div className="text-xs font-bold font-mono text-red-400">{strategy.maxDD}%</div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">Win Rate</div>
            <div className="text-xs font-bold font-mono">{strategy.winRate}%</div>
          </div>
        </div>

        {/* Last signal */}
        <div className="mt-3 flex items-center gap-2 p-2 rounded-lg bg-slate-700/20">
          <Activity size={10} className="text-blue-400" />
          <span className="text-[10px] text-slate-400">Latest: {strategy.lastSignal}</span>
        </div>
      </div>

      {/* Expand */}
      <div
        className="px-4 py-2 border-t border-slate-700/30 flex items-center justify-between cursor-pointer hover:bg-slate-800/40"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-[10px] text-slate-500">Details</span>
        {expanded ? <ChevronUp size={12} className="text-slate-500" /> : <ChevronDown size={12} className="text-slate-500" />}
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-700/30 pt-3">
          <div className="space-y-2">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Annual Return</span>
              <span className="font-mono text-emerald-400">+{strategy.annual}%</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Total Trades</span>
              <span className="font-mono">{strategy.trades}</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Live Since</span>
              <span className="font-mono">2026-01-{String(20 - strategy.liveDays).padStart(2, "0")}</span>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <button className="flex-1 h-7 rounded-lg bg-amber-600/20 text-amber-400 border border-amber-500/20 text-[10px] font-medium hover:bg-amber-600/30 transition-colors flex items-center justify-center gap-1">
              <Pause size={10} />
              Pause
            </button>
            <button className="flex-1 h-7 rounded-lg bg-red-600/20 text-red-400 border border-red-500/20 text-[10px] font-medium hover:bg-red-600/30 transition-colors">
              Retire
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ActiveColumn() {
  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-blue-500/20 flex items-center justify-center">
            <Zap size={10} className="text-blue-400" />
          </div>
          <span className="text-xs font-semibold text-blue-400">ACTIVE</span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            {activeStrategies.length}
          </span>
        </div>
        <div className="text-[10px] text-emerald-400 flex items-center gap-1">
          <TrendingUp size={10} />
          总Alpha: +29.4%
        </div>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {activeStrategies.map((s) => (
          <StrategyCard key={s.id} strategy={s} />
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
            All systems operational
          </div>
          <span className="text-[10px] text-slate-600">Updated 2m ago</span>
        </div>
      </div>
    </div>
  );
}
