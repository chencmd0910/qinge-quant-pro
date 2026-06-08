"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { Grid3X3 } from "lucide-react";
import api from "@/lib/axios";

export default function CorrelationMatrix() {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [matrix, setMatrix] = useState<number[][]>([]);
  const [avgCorr, setAvgCorr] = useState(0);

  useEffect(() => {
    api.get("/api/portfolio/correlation").then(({ data }) => {
      setStrategies(data.strategies || []);
      setMatrix(data.matrix || []);
      setAvgCorr(data.avg_correlation || 0);
    }).catch(() => {});
  }, []);

  if (!strategies.length) return null;

  const data: number[][] = [];
  for (let i = 0; i < strategies.length; i++) {
    for (let j = 0; j < strategies.length; j++) {
      data.push([j, i, matrix[i]?.[j] ?? 0]);
    }
  }

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#1e293b", borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: (params: any) => {
        const [x, y, val] = params.data;
        return `${strategies[y]} ↔ ${strategies[x]}: ${val.toFixed(2)}`;
      },
    },
    grid: { top: 10, right: 10, bottom: 40, left: 80 },
    xAxis: {
      type: "category", data: strategies,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#64748b", fontSize: 9, rotate: 25 },
    },
    yAxis: {
      type: "category", data: strategies,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#64748b", fontSize: 9 },
    },
    visualMap: {
      min: 0, max: 1, calculable: false, orient: "horizontal", left: "center", bottom: 0,
      textStyle: { color: "#475569", fontSize: 9 },
      inRange: { color: ["#0f172a", "#1e3a5f", "#1e40af", "#3b82f6", "#60a5fa"] },
      itemWidth: 12, itemHeight: 80,
    },
    series: [{
      type: "heatmap", data,
      label: { show: true, color: "#e2e8f0", fontSize: 11, fontWeight: "bold", formatter: (p: any) => p.data[2].toFixed(2) },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" } },
    }],
  };

  const level = avgCorr < 0.3 ? "低" : avgCorr < 0.5 ? "中" : "高";
  const lvlColor = avgCorr < 0.3 ? "text-emerald-400" : avgCorr < 0.5 ? "text-amber-400" : "text-red-400";

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1">
      <div className="flex items-center gap-2 mb-3">
        <Grid3X3 size={14} className="text-blue-400" />
        <span className="text-xs font-semibold">相关性矩阵</span>
        <span className={`text-[10px] ml-auto ${lvlColor}`}>均值: {avgCorr}（{level}）</span>
      </div>
      <ReactECharts option={option} style={{ height: 200 }} />
    </div>
  );
}
