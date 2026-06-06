"use client";

import { useState } from "react";
import {
  Eye,
  ChevronDown,
  ChevronUp,
  Clock,
  TrendingUp,
  TrendingDown,
  Play,
  ArrowRight,
  AlertTriangle,
} from "lucide-react";

interface WatchStrategy {
  id: string;
  name: string;
  version: string;
  sharpe: number;
  alpha: number;
  maxDD: number;
  annual: number;
  oosPass: boolean;
  wfPass: boolean;
  daysInWatch: number;
  reason: string;
  readyToPromote: boolean;
}

const watchlistStrategies: WatchStrategy[] = [
  {
    id: "nb-alpha",
    name: "Northbound Alpha",
    version: "NF4F",
    sharpe: 1.704,
    alpha: 11.0,
    maxDD: -9.73,
    annual: 11.73,
    oosPass: true,
    wfPass: true,
    daysInWatch: 14,
    reason: "Walk Forward 3/3 通过, 等待资金分配",
    readyToPromote: true,
  },
  {
    id: "ind-v1",
    name: "Industry Rotation V1",
    version: "V1",
    sharpe: 0.72,
    alpha: 6.2,
    maxDD: -22.0,
    annual: 8.7,
    oosPass: false,
    wfPass: false,
    daysInWatch: 7,
    reason: "OOS 测试中, Sharpe 偏低",
    readyToPromote: false,
  },
];

function WatchCard({ strategy }: { strategy: WatchStrategy }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl bg-slate-800/60 border border-slate-700/30 hover:border-amber-500/20 transition-colors">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">{strategy.name}</span>
              <span className="text-[9px] px-1.5 py-0.5 bg-amber-500/10 text-amber-400 rounded border border-amber-500/20">
                {strategy.version}
              </span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">观察 {strategy.daysInWatch} 天</div>
          </div>
          <div className="flex items-center gap-1">
            <Eye size={12} className="text-amber-400" />
            <span className="text-[10px] text-amber-400">WATCH</span>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-4 gap-2">
          <div className="p-2 rounded-lg bg-slate-700/30 text-center">
            <div className="text-[9px] text-slate-500">Sharpe</div>
            <div className="text-xs font-bold font-mono">{strategy.sharpe.toFixed(3)}</div>
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
            <div className="text-[9px] text-slate-500">Annual</div>
            <div className="text-xs font-bold font-mono text-emerald-400">+{strategy.annual}%</div>
          </div>
        </div>

        {/* Validation badges */}
        <div className="flex gap-2 mt-3">
          <div className={`flex items-center gap-1 px-2 py-1 rounded text-[9px] ${
            strategy.oosPass ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
          }`}>
            {strategy.oosPass ? "✓ OOS Pass" : "✗ OOS Fail"}
          </div>
          <div className={`flex items-center gap-1 px-2 py-1 rounded text-[9px] ${
            strategy.wfPass ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
          }`}>
            {strategy.wfPass ? "✓ WF Pass" : "✗ WF Fail"}
          </div>
        </div>

        {/* Reason */}
        <div className="mt-2 p-2 rounded-lg bg-slate-700/20 flex items-start gap-2">
          <AlertTriangle size={10} className="text-amber-400 mt-0.5 flex-shrink-0" />
          <span className="text-[10px] text-slate-400">{strategy.reason}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="px-4 py-2 border-t border-slate-700/30">
        {strategy.readyToPromote ? (
          <button className="w-full h-7 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 text-[10px] font-medium hover:bg-emerald-600/30 transition-colors flex items-center justify-center gap-1">
            <ArrowRight size={10} />
            Promote to ACTIVE
          </button>
        ) : (
          <button className="w-full h-7 rounded-lg bg-slate-700/30 text-slate-500 text-[10px] font-medium cursor-not-allowed flex items-center justify-center gap-1">
            <Clock size={10} />
            Continue Monitoring
          </button>
        )}
      </div>
    </div>
  );
}

export default function WatchlistColumn() {
  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-amber-500/20 flex items-center justify-center">
            <Eye size={10} className="text-amber-400" />
          </div>
          <span className="text-xs font-semibold text-amber-400">WATCHLIST</span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            {watchlistStrategies.length}
          </span>
        </div>
        <span className="text-[10px] text-slate-500">1 ready to promote</span>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {watchlistStrategies.map((s) => (
          <WatchCard key={s.id} strategy={s} />
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="text-[10px] text-slate-500 flex items-center gap-1.5">
          <Clock size={10} />
          观察周期: 14-30天
        </div>
      </div>
    </div>
  );
}
