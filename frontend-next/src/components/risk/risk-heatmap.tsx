"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { Grid3X3 } from "lucide-react";
import api from "@/lib/axios";

export default function RiskHeatmap() {
  const [assets, setAssets] = useState<string[]>([]);
  const [matrix, setMatrix] = useState<number[][]>([]);

  useEffect(() => {
    api.get("/api/risk/heatmap").then(({ data }) => {
      setAssets(data.assets || []);
      setMatrix(data.matrix || []);
    }).catch(() => {});
  }, []);

  if (!assets.length) return null;

  const data: number[][] = [];
  for (let i = 0; i < assets.length; i++) {
    for (let j = 0; j < assets.length; j++) {
      data.push([j, i, matrix[i]?.[j] ?? 0]);
    }
  }

  const avgColor = () => {
    const off = matrix.flatMap((r,i) => r.filter((_,j) => i !== j));
    const avg = off.reduce((s,v) => s+v, 0) / Math.max(off.length, 1);
    if (avg < 0.2) return "text-emerald-400";
    if (avg < 0.4) return "text-amber-400";
    return "text-red-400";
  };

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#1e293b", borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: (p: any) => `${assets[p.data[1]]} ↔ ${assets[p.data[0]]}: ${p.data[2].toFixed(2)}`,
    },
    grid: { top: 10, right: 10, bottom: 40, left: 70 },
    xAxis: {
      type: "category", data: assets,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#64748b", fontSize: 9, rotate: 25 },
    },
    yAxis: {
      type: "category", data: assets,
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
      label: { show: true, color: "#e2e8f0", fontSize: 10, formatter: (p: any) => p.data[2].toFixed(2) },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" } },
    }],
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1">
      <div className="flex items-center gap-2 mb-3">
        <Grid3X3 size={14} className="text-blue-400" />
        <span className="text-xs font-semibold">相关性热力图</span>
        <span className={`text-[10px] ml-auto ${avgColor()}`}>策略层级</span>
      </div>
      <ReactECharts option={option} style={{ height: 220 }} />
    </div>
  );
}
