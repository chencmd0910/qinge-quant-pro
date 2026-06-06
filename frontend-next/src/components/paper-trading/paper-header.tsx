"use client";

import { CandlestickChart, Play, Pause, RotateCcw, Settings } from "lucide-react";

export default function PaperHeader() {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
          <CandlestickChart size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold">Paper Trading Center</h1>
          <p className="text-xs text-slate-500">Simulated trading with real market data</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <Play size={12} className="text-emerald-400" />
          <span className="text-xs text-emerald-400">Running</span>
        </div>
        <button className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors">
          <Pause size={14} className="text-slate-400" />
        </button>
        <button className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors">
          <RotateCcw size={14} className="text-slate-400" />
        </button>
        <button className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors">
          <Settings size={14} className="text-slate-400" />
        </button>
      </div>
    </div>
  );
}
