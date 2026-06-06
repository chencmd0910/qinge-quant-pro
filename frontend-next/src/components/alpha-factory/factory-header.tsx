"use client";

import { Factory, Zap, TrendingUp, Shield, Activity } from "lucide-react";

export default function FactoryHeader() {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
          <Factory size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold">Alpha Factory</h1>
          <p className="text-xs text-slate-500">Strategy Lifecycle Management</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-blue-400 rounded-full" />
            <span className="text-slate-400">2 Active</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-amber-400 rounded-full" />
            <span className="text-slate-400">1 Watchlist</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-red-400 rounded-full" />
            <span className="text-slate-400">1 Retired</span>
          </div>
        </div>
      </div>
    </div>
  );
}
