"use client";

import ReactECharts from "echarts-for-react";
import { Activity } from "lucide-react";

export default function EquityCurve() {
  // Generate equity curve data
  const dates: string[] = [];
  const equity: number[] = [];
  const benchmark: number[] = [];
  let val = 1000000;
  let bench = 1000000;

  for (let i = 0; i < 45; i++) {
    const d = new Date(2026, 3, 1);
    d.setDate(d.getDate() + i);
    dates.push(d.toISOString().slice(5, 10));
    val += val * (0.1245 / 252) + val * (Math.random() * 0.008 - 0.003);
    bench += bench * (0.05 / 252) + bench * (Math.random() * 0.006 - 0.0025);
    equity.push(Math.round(val));
    benchmark.push(Math.round(bench));
  }

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1e293b",
      borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
    },
    legend: {
      data: ["Portfolio", "Benchmark"],
      top: 0,
      right: 0,
      textStyle: { color: "#64748b", fontSize: 10 },
      itemWidth: 12,
      itemHeight: 8,
    },
    grid: { top: 30, right: 10, bottom: 20, left: 50 },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#475569", fontSize: 9 },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      axisLabel: {
        color: "#475569",
        fontSize: 9,
        formatter: (v: number) => (v / 10000).toFixed(0) + "W",
      },
      splitLine: { lineStyle: { color: "#0f172a" } },
    },
    series: [
      {
        name: "Portfolio",
        data: equity,
        type: "line",
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#22d3ee", width: 1.5 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(34, 211, 238, 0.1)" },
              { offset: 1, color: "rgba(34, 211, 238, 0)" },
            ],
          },
        },
      },
      {
        name: "Benchmark",
        data: benchmark,
        type: "line",
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#475569", width: 1, type: "dashed" },
      },
    ],
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1">
      <div className="flex items-center gap-2 mb-3">
        <Activity size={14} className="text-cyan-400" />
        <span className="text-xs font-semibold">Equity Curve</span>
        <span className="text-[10px] text-emerald-400 ml-auto">+12.45% vs +2.1% BM</span>
      </div>
      <ReactECharts option={option} style={{ height: 200 }} />
    </div>
  );
}
