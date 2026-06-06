"use client";

import { useState } from "react";
import ReactECharts from "echarts-for-react";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Trophy,
} from "lucide-react";

const backtestResults = [
  {
    id: "etf-v6f",
    name: "V6F 量价_6F",
    annual: 19.57,
    sharpe: 2.5,
    alpha: 16.9,
    maxDD: -5.0,
    trades: 108,
    winRate: 100,
  },
  {
    id: "mf-v25",
    name: "V25 多因子",
    annual: 12.5,
    sharpe: 1.15,
    alpha: 10.0,
    maxDD: -18.5,
    trades: 240,
    winRate: 58,
  },
  {
    id: "ind-v1",
    name: "行业轮动 V1",
    annual: 8.7,
    sharpe: 0.72,
    alpha: 6.2,
    maxDD: -22.0,
    trades: 180,
    winRate: 52,
  },
];

export default function BacktestResult() {
  const [selected, setSelected] = useState(0);
  const result = backtestResults[selected];

  // Generate equity curve data
  const dates: string[] = [];
  const equity: number[] = [];
  let val = 1000000;
  for (let i = 0; i < 100; i++) {
    const d = new Date(2024, 0, 1);
    d.setDate(d.getDate() + i * 5);
    dates.push(d.toISOString().slice(5, 10));
    val += val * (result.annual / 100 / 252) * 5 + val * (Math.random() * 0.01 - 0.004);
    equity.push(Math.round(val));
  }

  const chartOption = {
    backgroundColor: "transparent",
    grid: { top: 10, right: 10, bottom: 20, left: 50 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1e293b",
      borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
    },
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
              { offset: 0, color: "rgba(34, 211, 238, 0.12)" },
              { offset: 1, color: "rgba(34, 211, 238, 0)" },
            ],
          },
        },
      },
    ],
  };

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <BarChart3 size={14} className="text-emerald-400" />
          <span className="text-xs font-semibold">Backtest Result</span>
        </div>
      </div>

      {/* Strategy selector */}
      <div className="px-3 py-2 border-b border-slate-800/50 flex gap-1">
        {backtestResults.map((r, idx) => (
          <button
            key={r.id}
            onClick={() => setSelected(idx)}
            className={`px-2 py-1 text-[10px] rounded transition-colors ${
              selected === idx
                ? "bg-blue-500/20 text-blue-400"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {r.name.split(" ")[0]}
          </button>
        ))}
      </div>

      {/* Results */}
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {/* KPI */}
        <div className="grid grid-cols-2 gap-2">
          <div className="p-2.5 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Annual Return</div>
            <div className="text-sm font-bold font-mono text-emerald-400">
              +{result.annual}%
            </div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Sharpe Ratio</div>
            <div className="text-sm font-bold font-mono">{result.sharpe.toFixed(3)}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Max Drawdown</div>
            <div className="text-sm font-bold font-mono text-red-400">{result.maxDD}%</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Alpha</div>
            <div className="text-sm font-bold font-mono text-emerald-400">+{result.alpha}%</div>
          </div>
        </div>

        {/* Chart */}
        <div className="rounded-lg bg-slate-800/30 p-2">
          <ReactECharts option={chartOption} style={{ height: 160 }} />
        </div>

        {/* Details */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] py-1.5 border-b border-slate-800/50">
            <span className="text-slate-500">Trades</span>
            <span className="font-mono">{result.trades}</span>
          </div>
          <div className="flex justify-between text-[11px] py-1.5 border-b border-slate-800/50">
            <span className="text-slate-500">Win Rate</span>
            <span className="font-mono text-emerald-400">{result.winRate}%</span>
          </div>
          <div className="flex justify-between text-[11px] py-1.5 border-b border-slate-800/50">
            <span className="text-slate-500">Period</span>
            <span className="font-mono">2018-01 ~ 2026-06</span>
          </div>
          <div className="flex justify-between text-[11px] py-1.5">
            <span className="text-slate-500">Commission</span>
            <span className="font-mono">万3</span>
          </div>
        </div>
      </div>

      {/* Action */}
      <div className="p-3 border-t border-slate-800">
        <button className="w-full h-8 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center gap-1.5 transition-colors">
          <Trophy size={12} />
          <span className="text-xs font-medium">提交到 Tournament</span>
        </button>
      </div>
    </div>
  );
}
