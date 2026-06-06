"use client";

import { TrendingUp, TrendingDown, Shield, Activity, DollarSign, BarChart3 } from "lucide-react";

export default function PortfolioKPI() {
  const kpis = [
    { label: "Total Value", value: "¥1,284,500", change: "+12.4%", positive: true, icon: DollarSign },
    { label: "Annual Return", value: "+18.2%", change: "+2.1% MTD", positive: true, icon: TrendingUp },
    { label: "Sharpe Ratio", value: "2.15", change: "+0.08", positive: true, icon: BarChart3 },
    { label: "Max Drawdown", value: "-8.5%", change: "Improved", positive: true, icon: Shield },
    { label: "Strategies", value: "3", change: "All Active", positive: true, icon: Activity },
    { label: "Correlation", value: "0.32", change: "Low", positive: true, icon: Activity },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
      {kpis.map((kpi) => (
        <div key={kpi.label} className="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-md bg-blue-500/10 flex items-center justify-center">
              <kpi.icon size={12} className="text-blue-400" />
            </div>
            <span className="text-[10px] text-slate-500">{kpi.label}</span>
          </div>
          <div className="text-lg font-bold font-mono">{kpi.value}</div>
          <div className={`text-[10px] mt-1 flex items-center gap-1 ${
            kpi.positive ? "text-emerald-400" : "text-red-400"
          }`}>
            {kpi.positive ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
            {kpi.change}
          </div>
        </div>
      ))}
    </div>
  );
}
