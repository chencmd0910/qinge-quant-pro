"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { Shield } from "lucide-react";
import api from "@/lib/axios";

export default function RiskContribution() {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [contributions, setContributions] = useState<number[]>([]);
  const [colors, setColors] = useState<string[]>([]);
  const [divBenefit, setDivBenefit] = useState(0);

  useEffect(() => {
    api.get("/api/portfolio/risk-contribution").then(({ data }) => {
      setStrategies(data.strategies || []);
      setContributions(data.contributions || []);
      setColors(data.colors || []);
      setDivBenefit(data.diversification_benefit || 0);
    }).catch(() => {});
  }, []);

  if (!strategies.length) return null;

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis", backgroundColor: "#1e293b", borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
    },
    grid: { top: 10, right: 30, bottom: 20, left: 80 },
    xAxis: {
      type: "value", max: 60,
      axisLabel: { color: "#475569", fontSize: 9, formatter: "{value}%" },
      splitLine: { lineStyle: { color: "#0f172a" } },
    },
    yAxis: {
      type: "category", data: strategies,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#94a3b8", fontSize: 10 },
    },
    series: [{
      type: "bar",
      data: contributions.map((v, i) => ({
        value: v,
        itemStyle: { color: colors[i] || "#3b82f6", borderRadius: [0, 4, 4, 0] },
      })),
      barWidth: 16,
      label: { show: true, position: "right", color: "#94a3b8", fontSize: 10, formatter: "{c}%" },
    }],
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Shield size={14} className="text-amber-400" />
        <span className="text-xs font-semibold">风险贡献</span>
        <span className="text-[10px] text-emerald-400 ml-auto">分散化收益: {divBenefit}%</span>
      </div>
      <ReactECharts option={option} style={{ height: 140 }} />
    </div>
  );
}
