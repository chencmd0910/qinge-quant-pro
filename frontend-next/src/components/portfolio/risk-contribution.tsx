"use client";

import ReactECharts from "echarts-for-react";
import { Shield } from "lucide-react";

export default function RiskContribution() {
  const strategies = ["ETF V6F", "MF V25", "NB Alpha"];
  const riskContrib = [28, 45, 27]; // percentage
  const colors = ["#3b82f6", "#8b5cf6", "#06b6d4"];

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1e293b",
      borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: (params: any) => {
        const p = params[0];
        return `${p.name}: ${p.value}% risk contribution`;
      },
    },
    grid: { top: 10, right: 20, bottom: 30, left: 80 },
    xAxis: {
      type: "value",
      max: 50,
      axisLine: { show: false },
      axisLabel: { color: "#475569", fontSize: 9, formatter: "{value}%" },
      splitLine: { lineStyle: { color: "#0f172a" } },
    },
    yAxis: {
      type: "category",
      data: strategies,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#94a3b8", fontSize: 10 },
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: riskContrib.map((v, i) => ({
          value: v,
          itemStyle: { color: colors[i], borderRadius: [0, 4, 4, 0] },
        })),
        barWidth: 20,
        label: {
          show: true,
          position: "right",
          color: "#94a3b8",
          fontSize: 10,
          formatter: "{c}%",
        },
      },
    ],
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Shield size={14} className="text-amber-400" />
        <span className="text-xs font-semibold">Risk Contribution</span>
        <span className="text-[10px] text-slate-500 ml-auto">Diversification benefit: 18%</span>
      </div>
      <ReactECharts option={option} style={{ height: 120 }} />
    </div>
  );
}
