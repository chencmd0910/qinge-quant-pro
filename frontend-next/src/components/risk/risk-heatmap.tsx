"use client";

import ReactECharts from "echarts-for-react";
import { Grid3X3 } from "lucide-react";

const assets = ["510300", "510500", "159915", "515080", "600519", "000858"];

// Simulated correlation data
const corrData: number[][] = [];
for (let i = 0; i < 6; i++) {
  for (let j = 0; j < 6; j++) {
    if (i === j) {
      corrData.push([j, i, 1.0]);
    } else if (j > i) {
      const val = Math.round((Math.random() * 0.6 + 0.1) * 100) / 100;
      corrData.push([j, i, val]);
      corrData.push([i, j, val]);
    }
  }
}

export default function RiskHeatmap() {
  const option = {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#1e293b",
      borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: (params: any) => {
        const [x, y, val] = params.data;
        return `${assets[y]} ↔ ${assets[x]}: ${val.toFixed(2)}`;
      },
    },
    grid: { top: 10, right: 10, bottom: 40, left: 60 },
    xAxis: {
      type: "category",
      data: assets,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#64748b", fontSize: 9 },
      axisTick: { show: false },
    },
    yAxis: {
      type: "category",
      data: assets,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#64748b", fontSize: 9 },
      axisTick: { show: false },
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
        data: corrData,
        label: {
          show: true,
          color: "#e2e8f0",
          fontSize: 10,
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
        <span className="text-xs font-semibold">Correlation Heatmap</span>
        <span className="text-[10px] text-slate-500 ml-auto">Asset Level</span>
      </div>
      <ReactECharts option={option} style={{ height: 220 }} />
    </div>
  );
}
