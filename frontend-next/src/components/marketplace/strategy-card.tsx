"use client";

import { Star, TrendingUp, TrendingDown, Copy, Play, Rocket, User } from "lucide-react";
import { MarketplaceStrategy } from "./marketplace-layout";

const statusColors: Record<string, string> = {
  ACTIVE: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  VALIDATED: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  RESEARCH: "bg-slate-500/10 text-slate-400 border-slate-500/20",
};

export default function StrategyCard({
  strategy,
  onClick,
  isSelected,
}: {
  strategy: MarketplaceStrategy;
  onClick: () => void;
  isSelected: boolean;
}) {
  return (
    <div
      onClick={onClick}
      className={`rounded-xl p-4 cursor-pointer transition-all duration-200 ${
        isSelected
          ? "bg-slate-800/80 border-2 border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.1)]"
          : "bg-slate-900/60 border border-slate-800 hover:border-slate-600"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="text-sm font-semibold">{strategy.name}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">{strategy.category}</div>
        </div>
        <div className={`text-[9px] px-1.5 py-0.5 rounded border ${statusColors[strategy.status]}`}>
          {strategy.status}
        </div>
      </div>

      {/* Rating */}
      <div className="flex items-center gap-1 mb-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Star
            key={i}
            size={12}
            className={i < strategy.rating ? "text-amber-400 fill-amber-400" : "text-slate-700"}
          />
        ))}
        <span className="text-[10px] text-slate-500 ml-1">{strategy.rating}.0</span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="p-1.5 rounded bg-slate-800/60 text-center">
          <div className="text-[8px] text-slate-500">Sharpe</div>
          <div className="text-xs font-bold font-mono">{strategy.sharpe.toFixed(2)}</div>
        </div>
        <div className="p-1.5 rounded bg-slate-800/60 text-center">
          <div className="text-[8px] text-slate-500">Alpha</div>
          <div className="text-xs font-bold font-mono text-emerald-400">+{strategy.alpha}%</div>
        </div>
        <div className="p-1.5 rounded bg-slate-800/60 text-center">
          <div className="text-[8px] text-slate-500">MaxDD</div>
          <div className="text-xs font-bold font-mono text-red-400">{strategy.maxDD}%</div>
        </div>
      </div>

      {/* Author + clones */}
      <div className="flex items-center justify-between text-[10px] text-slate-500">
        <div className="flex items-center gap-1">
          <User size={10} />
          {strategy.author}
        </div>
        <div className="flex items-center gap-1">
          <Copy size={10} />
          {strategy.clones} clones
        </div>
      </div>
    </div>
  );
}
