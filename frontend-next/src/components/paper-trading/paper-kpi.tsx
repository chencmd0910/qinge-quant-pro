"use client";

import { useEffect, useState } from "react";
import { DollarSign, TrendingUp, BarChart3, Clock, Target, Calendar } from "lucide-react";
import api from "@/lib/axios";

interface Summary {
  initial_capital: number;
  current_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  win_rate: number;
  trade_days: number;
  sharpe: number;
  max_dd: number;
  current_date?: string;
}

export default function PaperKPI() {
  const [data, setData] = useState<Summary | null>(null);

  useEffect(() => {
    api.get("/api/paper-trading/summary")
      .then(({ data }) => setData(data))
      .catch(() => {});
  }, []);

  if (!data) {
    return <div className="grid grid-cols-6 gap-3">{Array(6).fill(0).map((_,i) => <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 animate-pulse"><div className="h-3 w-16 bg-slate-800 rounded mb-2"/><div className="h-5 w-20 bg-slate-800 rounded"/></div>)}</div>;
  }

  const fm = (v: number) => `\u00A5${(v / 10000).toFixed(2)}\u4E07`;
  const fpct = (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;

  const kpis = [
    { label: data.current_date ? `\u6A21\u62DF\u65E5\u671F ${data.current_date}` : "\u5F53\u524D\u5E02\u503C", value: fm(data.current_value), icon: Calendar, color: "text-blue-400" },
    { label: "\u7D2F\u8BA1\u76C8\u4E8F", value: fpct(data.total_pnl_pct), change: fm(data.total_pnl), icon: TrendingUp, color: data.total_pnl >= 0 ? "text-emerald-400" : "text-red-400" },
    { label: "\u4ECA\u65E5\u76C8\u4E8F", value: fpct(data.daily_pnl_pct), change: fm(data.daily_pnl), icon: Clock, color: data.daily_pnl >= 0 ? "text-emerald-400" : "text-red-400" },
    { label: "\u590F\u666E\u6BD4\u7387", value: data.sharpe.toFixed(2), icon: BarChart3, color: data.sharpe >= 1 ? "text-emerald-400" : "text-amber-400" },
    { label: "\u6700\u5927\u56DE\u64A4", value: fpct(data.max_dd), icon: Target, color: Math.abs(data.max_dd) < 20 ? "text-emerald-400" : "text-red-400" },
    { label: "\u4EA4\u6613\u5929\u6570", value: data.trade_days.toString(), icon: DollarSign, color: "text-slate-400" },
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
            <div className={`text-[10px] mt-1 flex items-center gap-1 ${kpi.color}`}>
              <TrendingUp size={10} />
              {kpi.change}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
