"use client";

import ReactECharts from "echarts-for-react";

export default function EquityChart() {
  // Generate realistic equity curve data
  const dates: string[] = [];
  const values: number[] = [];
  let val = 1000000;
  const start = new Date(2025, 0, 1);

  for (let i = 0; i < 150; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    if (d.getDay() === 0 || d.getDay() === 6) continue;
    dates.push(d.toISOString().slice(5, 10));
    val += val * (Math.random() * 0.008 - 0.003);
    values.push(Math.round(val));
  }

  const option = {
    backgroundColor: "transparent",
    grid: { top: 20, right: 20, bottom: 30, left: 60 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1e293b",
      borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 12 },
      formatter: (params: any) => {
        const p = params[0];
        return `<div style="font-size:11px;color:#94a3b8">${p.name}</div>
                <div style="font-size:14px;font-weight:600;color:#22d3ee">
                  ¥${(p.value / 10000).toFixed(2)}万
                </div>`;
      },
    },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#475569", fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      axisLabel: {
        color: "#475569",
        fontSize: 10,
        formatter: (v: number) => (v / 10000).toFixed(0) + "万",
      },
      splitLine: { lineStyle: { color: "#0f172a" } },
    },
    series: [
      {
        data: values,
        type: "line",
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#22d3ee", width: 2 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(34, 211, 238, 0.15)" },
              { offset: 1, color: "rgba(34, 211, 238, 0)" },
            ],
          },
        },
      },
    ],
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold">权益曲线</h3>
          <p className="text-xs text-slate-500 mt-0.5">2025-01 ~ 2026-06</p>
        </div>
        <div className="flex gap-1">
          {["1M", "3M", "6M", "1Y", "ALL"].map((t) => (
            <button
              key={t}
              className={`px-2.5 py-1 text-[10px] rounded-md transition-colors ${
                t === "ALL"
                  ? "bg-blue-500/20 text-blue-400"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <ReactECharts option={option} style={{ height: 360 }} />
    </div>
  );
}
