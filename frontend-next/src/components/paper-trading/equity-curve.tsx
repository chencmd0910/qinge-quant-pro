"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { Activity } from "lucide-react";
import api from "@/lib/axios";

export default function EquityCurve() {
  const [equity, setEquity] = useState<number[]>([]);
  const [benchmark, setBenchmark] = useState<number[]>([]);
  const [dates, setDates] = useState<string[]>([]);

  useEffect(() => {
    api.get("/api/paper-trading/equity")
      .then(({ data }) => {
        setEquity(data.equity || []);
        setBenchmark(data.benchmark || []);
        // 优先用后端返回的日期，否则回退到硬编码
        if (data.dates && data.dates.length === data.equity.length) {
          setDates(data.dates.map((d: string) => d.slice(5, 10)));
        } else {
          setDates(equity.map((_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - equity.length + i + 1);
            return d.toISOString().slice(5, 10);
          }));
        }
      })
      .catch(() => {});
  }, []);

  if (!equity.length) {
    return <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1 flex items-center justify-center"><span className="text-xs text-slate-500">暂无数据</span></div>;
  }

  const displayDates = dates.length ? dates : equity.map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - equity.length + i + 1);
    return d.toISOString().slice(5, 10);
  });

  const option = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", backgroundColor: "#1e293b", borderColor: "#334155", textStyle: { color: "#e2e8f0", fontSize: 11 } },
    legend: { data: ["组合", "基准"], top: 0, right: 0, textStyle: { color: "#64748b", fontSize: 10 }, itemWidth: 12, itemHeight: 8 },
    grid: { top: 30, right: 10, bottom: 20, left: 55 },
    xAxis: { type: "category", data: displayDates, axisLine: { lineStyle: { color: "#1e293b" } }, axisLabel: { color: "#475569", fontSize: 9 } },
    yAxis: { type: "value", axisLabel: { color: "#475569", fontSize: 9, formatter: (v: number) => (v/10000).toFixed(0)+"万" }, splitLine: { lineStyle: { color: "#0f172a" } } },
    series: [
      { name: "组合", data: equity, type: "line", smooth: true, symbol: "none", lineStyle: { color: "#22d3ee", width: 1.5 }, areaStyle: { color: { type: "linear", x:0,y:0,x2:0,y2:1, colorStops: [{offset:0,color:"rgba(34,211,238,0.1)"},{offset:1,color:"rgba(34,211,238,0)"}] } } },
      { name: "基准", data: benchmark, type: "line", smooth: true, symbol: "none", lineStyle: { color: "#475569", width: 1, type: "dashed" } },
    ],
  };

  const pnl = equity.length >= 2 ? ((equity[equity.length-1] / equity[0] - 1) * 100).toFixed(2) : "0";
  const benchPnl = benchmark.length >= 2 ? ((benchmark[benchmark.length-1] / benchmark[0] - 1) * 100).toFixed(2) : "0";

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1">
      <div className="flex items-center gap-2 mb-3">
        <Activity size={14} className="text-cyan-400" />
        <span className="text-xs font-semibold">权益曲线</span>
        <span className="text-[10px] text-emerald-400 ml-auto">+{pnl}% vs +{benchPnl}% 基准</span>
      </div>
      <ReactECharts option={option} style={{ height: 200 }} />
    </div>
  );
}
