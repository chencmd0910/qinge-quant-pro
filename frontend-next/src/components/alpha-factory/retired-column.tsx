"use client";

import { useState } from "react";
import {
  Archive,
  ChevronDown,
  ChevronUp,
  TrendingDown,
  Clock,
  RotateCcw,
  Trash2,
} from "lucide-react";

interface RetiredStrategy {
  id: string;
  name: string;
  version: string;
  sharpe: number;
  alpha: number;
  maxDD: number;
  annual: number;
  retiredDate: string;
  retiredReason: string;
  liveDays: number;
  peakAlpha: number;
  canRestore: boolean;
}

const retiredStrategies: RetiredStrategy[] = [
  {
    id: "breakout-v3",
    name: "Breakout V3",
    version: "V3",
    sharpe: 0.45,
    alpha: -2.1,
    maxDD: -35.0,
    annual: -5.2,
    retiredDate: "2026-04-15",
    retiredReason: "Alpha 衰减超过阈值, 连续30天负收益",
    liveDays: 45,
    peakAlpha: 8.5,
    canRestore: false,
  },
  {
    id: "mf-v10",
    name: "Multi-Factor V10",
    version: "V10",
    sharpe: 0.82,
    alpha: 3.5,
    maxDD: -25.0,
    annual: 5.2,
    retiredDate: "2026-03-20",
    retiredReason: "被 V25 版本替代, 策略逻辑升级",
    liveDays: 90,
    peakAlpha: 12.0,
    canRestore: true,
  },
];

function RetiredCard({ strategy }: { strategy: RetiredStrategy }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl bg-slate-800/40 border border-slate-700/20 hover:border-red-500/10 transition-colors opacity-80">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-300">{strategy.name}</span>
              <span className="text-[9px] px-1.5 py-0.5 bg-red-500/10 text-red-400 rounded border border-red-500/20">
                {strategy.version}
              </span>
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              Retired {strategy.retiredDate} · Live {strategy.liveDays} days
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Archive size={12} className="text-red-400" />
            <span className="text-[10px] text-red-400">RETIRED</span>
          </div>
        </div>

        {/* Metrics - muted */}
        <div className="grid grid-cols-4 gap-2">
          <div className="p-2 rounded-lg bg-slate-700/20 text-center">
            <div className="text-[9px] text-slate-600">Sharpe</div>
            <div className="text-xs font-bold font-mono text-slate-400">{strategy.sharpe.toFixed(2)}</div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/20 text-center">
            <div className="text-[9px] text-slate-600">Alpha</div>
            <div className={`text-xs font-bold font-mono ${strategy.alpha >= 0 ? "text-slate-400" : "text-red-400"}`}>
              {strategy.alpha >= 0 ? "+" : ""}{strategy.alpha}%
            </div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/20 text-center">
            <div className="text-[9px] text-slate-600">Peak α</div>
            <div className="text-xs font-bold font-mono text-slate-500">+{strategy.peakAlpha}%</div>
          </div>
          <div className="p-2 rounded-lg bg-slate-700/20 text-center">
            <div className="text-[9px] text-slate-600">MaxDD</div>
            <div className="text-xs font-bold font-mono text-red-400">{strategy.maxDD}%</div>
          </div>
        </div>

        {/* Reason */}
        <div className="mt-3 p-2 rounded-lg bg-red-500/5 border border-red-500/10">
          <div className="text-[10px] text-red-400">{strategy.retiredReason}</div>
        </div>
      </div>

      {/* Expand */}
      <div
        className="px-4 py-2 border-t border-slate-700/20 flex items-center justify-between cursor-pointer hover:bg-slate-800/30"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-[10px] text-slate-600">Details</span>
        {expanded ? <ChevronUp size={12} className="text-slate-600" /> : <ChevronDown size={12} className="text-slate-600" />}
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-700/20 pt-3">
          <div className="space-y-2">
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-600">Annual Return</span>
              <span className={`font-mono ${strategy.annual >= 0 ? "text-slate-400" : "text-red-400"}`}>
                {strategy.annual >= 0 ? "+" : ""}{strategy.annual}%
              </span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-600">Peak → Retired</span>
              <span className="font-mono text-red-400">
                +{strategy.peakAlpha}% → {strategy.alpha}%
              </span>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            {strategy.canRestore && (
              <button className="flex-1 h-7 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/20 text-[10px] font-medium hover:bg-blue-600/30 transition-colors flex items-center justify-center gap-1">
                <RotateCcw size={10} />
                Restore
              </button>
            )}
            <button className="flex-1 h-7 rounded-lg bg-slate-700/30 text-slate-500 border border-slate-600/20 text-[10px] font-medium hover:bg-slate-700/50 transition-colors flex items-center justify-center gap-1">
              <Trash2 size={10} />
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function RetiredColumn() {
  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-red-500/20 flex items-center justify-center">
            <Archive size={10} className="text-red-400" />
          </div>
          <span className="text-xs font-semibold text-red-400">RETIRED</span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
            {retiredStrategies.length}
          </span>
        </div>
        <span className="text-[10px] text-slate-600">1 can restore</span>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {retiredStrategies.map((s) => (
          <RetiredCard key={s.id} strategy={s} />
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="text-[10px] text-slate-600 flex items-center gap-1.5">
          <TrendingDown size={10} />
          已退役策略不参与实盘交易
        </div>
      </div>
    </div>
  );
}
