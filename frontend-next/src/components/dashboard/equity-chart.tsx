"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import api from "@/lib/axios";

interface EquityPoint {
  date: string;
  value: number;
}

export default function EquityChart() {
  const [points, setPoints] = useState<EquityPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState("全部");

  useEffect(() => {
    api.get("/api/dashboard/summary")
      .then(({ data }) => {
        if (data.equity_curve?.length) {
          setPoints(data.equity_curve);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const displayed = (() => {
    const map: Record<string, number> = { "1月": 20, "3月": 60, "6月": 120 };
    const take = map[range];
    if (!take || take >= points.length) return points;
    return points.slice(points.length - take);
  })();

  const dates = displayed.map((p) => p.date.slice(5));
  const values = displayed.map((p) => p.value);

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

  if (loading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 animate-pulse">
        <div className="h-4 w-24 bg-slate-800 rounded mb-4" />
        <div className="h-[360px] bg-slate-800/50 rounded" />
      </div>
    );
  }

  if (!points.length) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">权益曲线</h3>
        </div>
        <div className="h-[360px] flex items-center justify-center text-slate-500 text-sm">
          📊 暂无数据 — 运行回测后将显示权益曲线
        </div>
      </div>
    );
  }

  const startDate = displayed[0]?.date ?? "";
  const endDate = displayed[displayed.length - 1]?.date ?? "";

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold">权益曲线</h3>
          <p className="text-xs text-slate-500 mt-0.5">{startDate} ~ {endDate}</p>
        </div>
        <div className="flex gap-1">
          {["1月", "3月", "6月", "全部"].map((t) => (
            <button
              key={t}
              onClick={() => setRange(t)}
              className={`px-2.5 py-1 text-[10px] rounded-md transition-colors ${
                range === t
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
