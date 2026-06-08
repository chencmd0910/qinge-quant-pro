"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { BarChart3, Trophy } from "lucide-react";
import api from "@/lib/axios";
import { toast } from "@/lib/toast";

interface BacktestResult {
  id: string;
  name: string;
  type: string;
  annual: number;
  sharpe: number;
  alpha: number;
  maxDD: number;
  trades: number;
  winRate: number;
  status: string;
}

export default function BacktestResult() {
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [selected, setSelected] = useState(0);
  const [equity, setEquity] = useState<number[]>([]);

  useEffect(() => {
    api.get("/api/strategy-lab/results")
      .then(({ data }) => setResults(data.results || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!results.length) return;
    const id = results[selected]?.id;
    if (!id) return;
    api.get(`/api/strategy-lab/equity/${id}`)
      .then(({ data }) => setEquity(data.equity || []))
      .catch(() => {});
  }, [selected, results]);

  if (!results.length) {
    return <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-center"><span className="text-xs text-slate-500">暂无回测数据</span></div>;
  }

  const r = results[selected];

  const dates: string[] = equity.map((_, i) => {
    const d = new Date(2018, 0, 1);
    d.setDate(d.getDate() + i * 5);
    return d.toISOString().slice(5, 10);
  });

  const chartOption = {
    backgroundColor: "transparent",
    grid: { top: 10, right: 10, bottom: 20, left: 50 },
    tooltip: {
      trigger: "axis", backgroundColor: "#1e293b", borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
    },
    xAxis: {
      type: "category", data: dates,
      axisLine: { lineStyle: { color: "#1e293b" } },
      axisLabel: { color: "#475569", fontSize: 9 },
    },
    yAxis: {
      type: "value", axisLine: { show: false },
      axisLabel: { color: "#475569", fontSize: 9, formatter: (v: number) => (v / 10000).toFixed(0) + "万" },
      splitLine: { lineStyle: { color: "#0f172a" } },
    },
    series: [{
      data: equity, type: "line", smooth: true, symbol: "none",
      lineStyle: { color: "#22d3ee", width: 1.5 },
      areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(34,211,238,0.12)" }, { offset: 1, color: "rgba(34,211,238,0)" }] } },
    }],
  };

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <BarChart3 size={14} className="text-emerald-400" />
          <span className="text-xs font-semibold">回测结果</span>
        </div>
      </div>

      <div className="px-3 py-2 border-b border-slate-800/50 flex gap-1 overflow-x-auto">
        {results.map((s, idx) => (
          <button
            key={s.id}
            onClick={() => setSelected(idx)}
            className={`px-2 py-1 text-[10px] rounded whitespace-nowrap transition-colors ${
              selected === idx ? "bg-blue-500/20 text-blue-400" : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {s.name.length > 10 ? s.name.slice(0, 10) + "…" : s.name}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <div className="p-2.5 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">年化收益</div>
            <div className="text-sm font-bold font-mono text-emerald-400">+{r.annual}%</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">夏普比率</div>
            <div className="text-sm font-bold font-mono">{r.sharpe.toFixed(3)}</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">最大回撤</div>
            <div className="text-sm font-bold font-mono text-red-400">{r.maxDD}%</div>
          </div>
          <div className="p-2.5 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Alpha</div>
            <div className="text-sm font-bold font-mono text-emerald-400">{r.alpha >= 0 ? "+" : ""}{r.alpha}%</div>
          </div>
        </div>

        <div className="rounded-lg bg-slate-800/30 p-2">
          <ReactECharts option={chartOption} style={{ height: 160 }} />
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] py-1.5 border-b border-slate-800/50">
            <span className="text-slate-500">交易笔数</span>
            <span className="font-mono">{r.trades}</span>
          </div>
          <div className="flex justify-between text-[11px] py-1.5 border-b border-slate-800/50">
            <span className="text-slate-500">胜率</span>
            <span className="font-mono text-emerald-400">{r.winRate}%</span>
          </div>
          <div className="flex justify-between text-[11px] py-1.5 border-b border-slate-800/50">
            <span className="text-slate-500">周期</span>
            <span className="font-mono">2018-01 ~ 2026-06</span>
          </div>
          <div className="flex justify-between text-[11px] py-1.5">
            <span className="text-slate-500">状态</span>
            <span className="font-mono text-emerald-400">{r.status}</span>
          </div>
        </div>
      </div>

      <div className="p-3 border-t border-slate-800">
        <button
          onClick={() => toast("success", `${r.name} 已提交到 Tournament 考核`)}
          className="w-full h-8 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center gap-1.5 transition-colors"
        >
          <Trophy size={12} />
          <span className="text-xs font-medium">提交到 Tournament</span>
        </button>
      </div>
    </div>
  );
}
