"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Shield, Activity, DollarSign, BarChart3 } from "lucide-react";
import api from "@/lib/axios";

export default function PortfolioKPI() {
  const [kpis, setKpis] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/api/dashboard/summary"),
      api.get("/api/portfolio/positions"),
    ])
      .then(([dashRes, posRes]) => {
        const d = dashRes.data;
        const positions = posRes.data?.value ?? posRes.data ?? [];
        const posCount = Array.isArray(positions) ? positions.length : 0;
        const totalValue = d.total_asset ?? 10_000_000;

        setKpis([
          { label: "总资产", value: `¥${(totalValue / 10000).toFixed(2)}万`, change: `累计 ${d.cumulative_return?.toFixed(2) ?? 0}%`, positive: (d.cumulative_return ?? 0) >= 0, icon: DollarSign },
          { label: "年化收益", value: `${d.annual_return?.toFixed(2) ?? "0"}%`, change: `${d.running_strategies ?? 0} 策略运行中`, positive: true, icon: TrendingUp },
          { label: "夏普比率", value: (d.sharpe_ratio ?? 0).toFixed(2), change: "月度调仓", positive: (d.sharpe_ratio ?? 0) >= 0.5, icon: BarChart3 },
          { label: "最大回撤", value: `${d.max_drawdown?.toFixed(2) ?? "0"}%`, change: d.max_drawdown > 20 ? "偏高" : "正常", positive: (d.max_drawdown ?? 99) <= 20, icon: Shield },
          { label: "持仓数", value: `${posCount}`, change: `${d.position_count ?? posCount} 只`, positive: posCount > 0, icon: Activity },
          { label: "胜率", value: `${d.win_rate?.toFixed(1) ?? "0"}%`, change: `盈亏比 ${d.profit_loss_ratio?.toFixed(2) ?? "0"}`, positive: (d.win_rate ?? 0) >= 50, icon: Activity },
        ]);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-6 gap-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 animate-pulse">
            <div className="h-3 w-16 bg-slate-800 rounded mb-2" />
            <div className="h-5 w-20 bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    );
  }

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
