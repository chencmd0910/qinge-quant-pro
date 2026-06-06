"use client";

import { TrendingUp, TrendingDown, Activity, Shield } from "lucide-react";

const data = [
  {
    title: "总资产",
    value: "¥12,530,000",
    change: "+1.97%",
    up: true,
    icon: TrendingUp,
    color: "from-emerald-500/10 to-emerald-500/5",
    border: "border-emerald-500/20",
    iconColor: "text-emerald-400",
  },
  {
    title: "今日收益",
    value: "+¥243,600",
    change: "+2.31%",
    up: true,
    icon: TrendingUp,
    color: "from-blue-500/10 to-blue-500/5",
    border: "border-blue-500/20",
    iconColor: "text-blue-400",
  },
  {
    title: "运行策略",
    value: "5",
    change: "2 ACTIVE · 2 WATCH",
    up: true,
    icon: Activity,
    color: "from-violet-500/10 to-violet-500/5",
    border: "border-violet-500/20",
    iconColor: "text-violet-400",
  },
  {
    title: "风险评分",
    value: "81",
    change: "LOW RISK",
    up: true,
    icon: Shield,
    color: "from-amber-500/10 to-amber-500/5",
    border: "border-amber-500/20",
    iconColor: "text-amber-400",
  },
];

export default function KPIGrid() {
  return (
    <div className="grid grid-cols-4 gap-4">
      {data.map((item) => (
        <div
          key={item.title}
          className={`
            bg-gradient-to-br ${item.color}
            border ${item.border}
            rounded-xl p-5
            hover:scale-[1.02] transition-transform duration-200
          `}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-slate-400 font-medium">{item.title}</span>
            <item.icon size={16} className={item.iconColor} />
          </div>
          <div className="text-2xl font-bold tracking-tight">{item.value}</div>
          <div className={`text-xs mt-1.5 ${item.up ? "text-emerald-400" : "text-red-400"}`}>
            {item.change}
          </div>
        </div>
      ))}
    </div>
  );
}
