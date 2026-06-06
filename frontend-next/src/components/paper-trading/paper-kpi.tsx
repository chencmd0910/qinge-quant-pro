"use client";

import { DollarSign, TrendingUp, TrendingDown, BarChart3, Activity, Clock } from "lucide-react";

export default function PaperKPI() {
  const kpis = [
    { label: "Initial Capital", value: "¥1,000,000", icon: DollarSign, color: "text-slate-400" },
    { label: "Current Value", value: "¥1,124,500", icon: DollarSign, color: "text-blue-400" },
    { label: "Total P&L", value: "+¥124,500", change: "+12.45%", icon: TrendingUp, color: "text-emerald-400" },
    { label: "Today P&L", value: "+¥3,200", change: "+0.28%", icon: TrendingUp, color: "text-emerald-400" },
    { label: "Win Rate", value: "68%", icon: BarChart3, color: "text-blue-400" },
    { label: "Trading Days", value: "45", icon: Clock, color: "text-slate-400" },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
      {kpis.map((kpi) => (
        <div key={kpi.label} className="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-md bg-slate-800 flex items-center justify-center">
              <kpi.icon size={12} className={kpi.color} />
            </div>
            <span className="text-[10px] text-slate-500">{kpi.label}</span>
          </div>
          <div className={`text-sm font-bold font-mono ${kpi.color}`}>{kpi.value}</div>
          {kpi.change && (
            <div className="text-[10px] text-emerald-400 mt-1 flex items-center gap-1">
              <TrendingUp size={10} />
              {kpi.change}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
