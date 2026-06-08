"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Activity, Shield, DollarSign } from "lucide-react";
import api from "@/lib/axios";

interface KPIItem {
  title: string;
  value: string;
  change: string;
  up: boolean;
  icon: any;
  color: string;
  border: string;
  iconColor: string;
}

export default function KPIGrid() {
  const [kpis, setKpis] = useState<KPIItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get("/api/dashboard/summary")
      .then(({ data }) => {
        const totalAsset = (data.total_asset ?? 10_000_000) as number;
        const dailyReturn = (data.daily_return ?? 0) as number;
        const sharpe = (data.sharpe_ratio ?? 0) as number;
        const maxDD = (data.max_drawdown ?? 0) as number;
        const positions = (data.position_count ?? 0) as number;
        const strategies = (data.running_strategies ?? 0) as number;
        const winRate = (data.win_rate ?? 0) as number;

        setKpis([
          {
            title: "总资产",
            value: `¥${(totalAsset / 10000).toFixed(2)}万`,
            change: `累计${(data.cumulative_return ?? 0).toFixed(2)}%`,
            up: (data.cumulative_return ?? 0) >= 0,
            icon: DollarSign,
            color: "from-emerald-500/10 to-emerald-500/5",
            border: "border-emerald-500/20",
            iconColor: "text-emerald-400",
          },
          {
            title: "今日收益",
            value: `¥${(dailyReturn / 100 * totalAsset).toLocaleString()}`,
            change: `${dailyReturn >= 0 ? "+" : ""}${dailyReturn.toFixed(2)}%`,
            up: dailyReturn >= 0,
            icon: TrendingUp,
            color: "from-blue-500/10 to-blue-500/5",
            border: "border-blue-500/20",
            iconColor: "text-blue-400",
          },
          {
            title: "运行状态",
            value: `${strategies}`,
            change: `${positions} 持仓 · 胜率${winRate.toFixed(0)}%`,
            up: winRate >= 50,
            icon: Activity,
            color: "from-violet-500/10 to-violet-500/5",
            border: "border-violet-500/20",
            iconColor: "text-violet-400",
          },
          {
            title: "风控指标",
            value: `夏普 ${sharpe.toFixed(2)}`,
            change: `最大回撤 ${maxDD.toFixed(2)}%`,
            up: sharpe >= 0.5,
            icon: Shield,
            color: "from-amber-500/10 to-amber-500/5",
            border: "border-amber-500/20",
            iconColor: "text-amber-400",
          },
        ]);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch dashboard:", err);
        setError("API 未连接");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl p-5 animate-pulse" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
            <div className="h-3 w-16 rounded mb-3" style={{ backgroundColor: "rgba(255,255,255,0.05)" }} />
            <div className="h-7 w-28 rounded mb-2" style={{ backgroundColor: "rgba(255,255,255,0.05)" }} />
            <div className="h-3 w-20 rounded" style={{ backgroundColor: "rgba(255,255,255,0.05)" }} />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl p-4 text-center" style={{ backgroundColor: "rgba(245,158,11,0.05)", border: "1px solid rgba(245,158,11,0.2)" }}>
        <span className="text-amber-400 text-sm">⚠ {error} — 后端服务可能未启动</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-4 gap-4">
      {kpis.map((item) => (
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
