"use client";

import { TrendingUp, BarChart3, PieChart, Droplets, AlertTriangle, CheckCircle2 } from "lucide-react";

const categories = [
  {
    name: "Market Risk",
    icon: TrendingUp,
    score: 85,
    status: "LOW",
    items: [
      { label: "VIX", value: "14.2", status: "ok" },
      { label: "Market Trend", value: "Bullish", status: "ok" },
      { label: "Sector Rotation", value: "Normal", status: "ok" },
    ],
  },
  {
    name: "Strategy Risk",
    icon: BarChart3,
    score: 80,
    status: "LOW",
    items: [
      { label: "Alpha Decay", value: "None", status: "ok" },
      { label: "Overfitting", value: "Low", status: "ok" },
      { label: "Signal Conflict", value: "None", status: "ok" },
    ],
  },
  {
    name: "Portfolio Risk",
    icon: PieChart,
    score: 78,
    status: "MODERATE",
    items: [
      { label: "Concentration", value: "40%", status: "warn" },
      { label: "Correlation", value: "0.32", status: "ok" },
      { label: "Leverage", value: "1.0x", status: "ok" },
    ],
  },
  {
    name: "Liquidity Risk",
    icon: Droplets,
    score: 90,
    status: "LOW",
    items: [
      { label: "ETF Liquidity", value: "High", status: "ok" },
      { label: "Spread", value: "0.05%", status: "ok" },
      { label: "Volume", value: "Normal", status: "ok" },
    ],
  },
];

const statusColors: Record<string, string> = {
  LOW: "text-emerald-400 bg-emerald-500/10",
  MODERATE: "text-amber-400 bg-amber-500/10",
  HIGH: "text-red-400 bg-red-500/10",
};

export default function RiskCategories() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1">
      <div className="text-xs font-semibold mb-3">Risk Categories</div>

      <div className="space-y-3">
        {categories.map((cat) => (
          <div key={cat.name} className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/20">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <cat.icon size={12} className="text-blue-400" />
                <span className="text-xs font-medium">{cat.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold">{cat.score}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded ${statusColors[cat.status]}`}>
                  {cat.status}
                </span>
              </div>
            </div>

            <div className="space-y-1">
              {cat.items.map((item) => (
                <div key={item.label} className="flex items-center justify-between text-[10px]">
                  <span className="text-slate-500">{item.label}</span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-300">{item.value}</span>
                    {item.status === "ok" ? (
                      <CheckCircle2 size={10} className="text-emerald-500" />
                    ) : (
                      <AlertTriangle size={10} className="text-amber-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
