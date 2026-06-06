"use client";

import {
  Star,
  Copy,
  Play,
  Rocket,
  TrendingUp,
  TrendingDown,
  Clock,
  Activity,
  Shield,
  BarChart3,
  User,
  Tag,
  Zap,
} from "lucide-react";
import { MarketplaceStrategy } from "./marketplace-layout";

export default function StrategyDetail({ strategy }: { strategy: MarketplaceStrategy | null }) {
  if (!strategy) {
    return (
      <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col items-center justify-center text-slate-600">
        <Zap size={32} className="mb-3 opacity-30" />
        <span className="text-sm">Select a strategy to view details</span>
      </div>
    );
  }

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="text-lg font-semibold">{strategy.name}</div>
            <div className="text-xs text-slate-500 mt-0.5">{strategy.category} · {strategy.version}</div>
          </div>
          <div className="flex items-center gap-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                size={14}
                className={i < strategy.rating ? "text-amber-400 fill-amber-400" : "text-slate-700"}
              />
            ))}
          </div>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">{strategy.description}</p>

        <div className="flex items-center gap-3 mt-3 text-[10px] text-slate-500">
          <div className="flex items-center gap-1">
            <User size={10} />
            {strategy.author}
          </div>
          <div className="flex items-center gap-1">
            <Copy size={10} />
            {strategy.clones} clones
          </div>
          <div className="flex items-center gap-1">
            <Clock size={10} />
            Live {strategy.liveDays}d
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="p-5 border-b border-slate-800">
        <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-3">Performance</div>
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Annual Return</div>
            <div className="text-lg font-bold font-mono text-emerald-400">+{strategy.annual}%</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Sharpe Ratio</div>
            <div className="text-lg font-bold font-mono">{strategy.sharpe.toFixed(3)}</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Alpha</div>
            <div className="text-lg font-bold font-mono text-emerald-400">+{strategy.alpha}%</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Max Drawdown</div>
            <div className="text-lg font-bold font-mono text-red-400">{strategy.maxDD}%</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Win Rate</div>
            <div className="text-lg font-bold font-mono">{strategy.winRate}%</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Trades</div>
            <div className="text-lg font-bold font-mono">{strategy.trades}</div>
          </div>
        </div>
      </div>

      {/* Factors */}
      <div className="p-5 border-b border-slate-800">
        <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Factors</div>
        <div className="flex flex-wrap gap-1.5">
          {strategy.factors.map((f) => (
            <span key={f} className="px-2 py-1 text-[10px] bg-slate-800 text-slate-400 rounded-md border border-slate-700/50">
              {f}
            </span>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="p-5 mt-auto">
        <div className="grid grid-cols-3 gap-2">
          <button className="h-9 rounded-lg bg-slate-800 border border-slate-700 text-xs font-medium hover:bg-slate-700 transition-colors flex items-center justify-center gap-1.5">
            <Copy size={12} />
            Clone
          </button>
          <button className="h-9 rounded-lg bg-blue-600/20 border border-blue-500/30 text-xs font-medium text-blue-400 hover:bg-blue-600/30 transition-colors flex items-center justify-center gap-1.5">
            <Play size={12} />
            Backtest
          </button>
          <button className="h-9 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-medium transition-colors flex items-center justify-center gap-1.5">
            <Rocket size={12} />
            Deploy
          </button>
        </div>
      </div>
    </div>
  );
}
