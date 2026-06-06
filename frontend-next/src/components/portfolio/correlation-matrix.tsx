"use client";

import ReactECharts from "echarts-for-react";
import { Grid3X3 } from "lucide-react";

const strategies = ["ETF V6F", "MF V25", "NB Alpha"];

// Correlation matrix (symmetric)
const correlation = [
  [1.0, 0.28, 0.15],
  [0.28, 1.0, 0.42],
  [0.15, 0.42, 1.0],
];

export default function CorrelationMatrix() {
  // Build heatmap data
  const data: number[][] = [];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      data.push([j, i, correlation[i][j]]);
    }
  }

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#1e293b",
      borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: (params: any) => {
        const [x, y, val] = params.data;
        return `${strategies[y]} ↔ ${strategies[x]}: ${val.toFixed(2)}`;
      },
    },
    grid: { top: 10, right: 10, bottom: 40, left: 60 },
    xAxis: {
      type: "category",
      data: strategies,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#64748b", fontSize: 10 },
      axisTick: { show: false },
      splitArea: { show: false },
    },
    yAxis: {
      type: "category",
      data: strategies,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#64748b", fontSize: 10 },
      axisTick: { show: false },
      splitArea: { show: false },
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: false,
      orient: "horizontal",
      left: "center",
      bottom: 0,
      textStyle: { color: "#475569", fontSize: 9 },
      inRange: {
        color: ["#0f172a", "#1e3a5f", "#1e40af", "#3b82f6", "#60a5fa"],
      },
      itemWidth: 12,
      itemHeight: 80,
    },
    series: [
      {
        type: "heatmap",
        data: data,
        label: {
          show: true,
          color: "#e2e8f0",
          fontSize: 12,
          fontWeight: "bold",
          formatter: (params: any) => params.data[2].toFixed(2),
        },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" },
        },
      },
    ],
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1">
      <div className="flex items-center gap-2 mb-3">
        <Grid3X3 size={14} className="text-blue-400" />
        <span className="text-xs font-semibold">Correlation Matrix</span>
        <span className="text-[10px] text-slate-500 ml-auto">Avg: 0.28 (Low)</span>
      </div>
      <ReactECharts option={option} style={{ height: 180 }} />
    </div>
  );
}
