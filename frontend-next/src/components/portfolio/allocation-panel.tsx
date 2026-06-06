"use client";

import { useState } from "react";
import ReactECharts from "echarts-for-react";
import { PieChart, GripVertical, Lock, Unlock, RefreshCw } from "lucide-react";

interface Allocation {
  id: string;
  name: string;
  weight: number;
  color: string;
  sharpe: number;
  alpha: number;
  locked: boolean;
}

const initialAllocations: Allocation[] = [
  { id: "etf-v6f", name: "ETF Rotation V6F", weight: 40, color: "#3b82f6", sharpe: 2.5, alpha: 16.9, locked: false },
  { id: "mf-v25", name: "Multi-Factor V25", weight: 35, color: "#8b5cf6", sharpe: 2.1, alpha: 12.5, locked: false },
  { id: "nb-alpha", name: "Northbound Alpha", weight: 25, color: "#06b6d4", sharpe: 1.7, alpha: 11.0, locked: false },
];

export default function AllocationPanel() {
  const [allocations, setAllocations] = useState<Allocation[]>(initialAllocations);

  const handleWeightChange = (id: string, newWeight: number) => {
    setAllocations((prev) => {
      const others = prev.filter((a) => a.id !== id);
      const lockedTotal = others.filter((a) => a.locked).reduce((s, a) => s + a.weight, 0);
      const unlocked = others.filter((a) => !a.locked);
      const remaining = 100 - newWeight - lockedTotal;
      const unlockedTotal = unlocked.reduce((s, a) => s + a.weight, 0);

      return prev.map((a) => {
        if (a.id === id) return { ...a, weight: newWeight };
        if (a.locked) return a;
        return { ...a, weight: Math.max(0, Math.round((a.weight / unlockedTotal) * remaining)) };
      });
    });
  };

  const toggleLock = (id: string) => {
    setAllocations((prev) =>
      prev.map((a) => (a.id === id ? { ...a, locked: !a.locked } : a))
    );
  };

  const chartOption = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "#1e293b",
      borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: "{b}: {c}% ({d}%)",
    },
    series: [
      {
        type: "pie",
        radius: ["50%", "75%"],
        center: ["50%", "50%"],
        itemStyle: { borderColor: "#0f172a", borderWidth: 3 },
        label: { show: false },
        emphasis: {
          itemStyle: { shadowBlur: 20, shadowColor: "rgba(0,0,0,0.5)" },
        },
        data: allocations.map((a) => ({
          value: a.weight,
          name: a.name,
          itemStyle: { color: a.color },
        })),
      },
    ],
  };

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <PieChart size={14} className="text-indigo-400" />
          <span className="text-xs font-semibold">Allocation</span>
        </div>
        <button className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors">
          Rebalance
        </button>
      </div>

      {/* Chart */}
      <div className="px-4 py-2">
        <ReactECharts option={chartOption} style={{ height: 200 }} />
      </div>

      {/* Allocations */}
      <div className="flex-1 overflow-auto px-4 pb-4 space-y-3">
        {allocations.map((a) => (
          <div key={a.id} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/30">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: a.color }} />
                <span className="text-xs font-medium">{a.name}</span>
              </div>
              <button onClick={() => toggleLock(a.id)} className="p-1 rounded hover:bg-slate-700 transition-colors">
                {a.locked ? <Lock size={12} className="text-amber-400" /> : <Unlock size={12} className="text-slate-500" />}
              </button>
            </div>

            {/* Weight slider */}
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={5}
                max={80}
                step={1}
                value={a.weight}
                disabled={a.locked}
                onChange={(e) => handleWeightChange(a.id, parseInt(e.target.value))}
                className="flex-1 h-1 bg-slate-700 rounded-full appearance-none cursor-pointer disabled:opacity-40
                           [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:appearance-none"
                style={{ "--tw-slider-thumb-bg": a.color } as any}
              />
              <span className="text-sm font-bold font-mono w-10 text-right">{a.weight}%</span>
            </div>

            {/* Metrics */}
            <div className="flex gap-3 mt-2 text-[10px] text-slate-500">
              <span>S: {a.sharpe}</span>
              <span>α: +{a.alpha}%</span>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex justify-between text-[10px]">
          <span className="text-slate-500">Total</span>
          <span className="font-mono font-semibold">
            {allocations.reduce((s, a) => s + a.weight, 0)}%
          </span>
        </div>
      </div>
    </div>
  );
}
