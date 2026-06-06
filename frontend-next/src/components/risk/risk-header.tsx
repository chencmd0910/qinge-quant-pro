"use client";

import { Shield, Bell, RefreshCw } from "lucide-react";

export default function RiskHeader() {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
          <Shield size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold">Risk Command Center</h1>
          <p className="text-xs text-slate-500">Real-time risk monitoring & auto actions</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <div className="w-2 h-2 bg-emerald-400 rounded-full" />
          <span className="text-xs text-emerald-400">All Clear</span>
        </div>
        <button className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors relative">
          <Bell size={14} className="text-slate-400" />
          <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-amber-400 rounded-full" />
        </button>
        <button className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors">
          <RefreshCw size={14} className="text-slate-400" />
        </button>
      </div>
    </div>
  );
}
