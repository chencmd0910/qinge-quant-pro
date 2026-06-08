"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { PieChart, Lock, Unlock } from "lucide-react";
import api from "@/lib/axios";
import { toast } from "@/lib/toast";

interface Allocation {
  id: string;
  name: string;
  weight: number;
  color: string;
  sharpe: number;
  alpha: number;
  locked: boolean;
}

export default function AllocationPanel() {
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/portfolio/allocation")
      .then(({ data }) => {
        setAllocations(data.allocations || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const toggleLock = (id: string) => {
    setAllocations((prev) => prev.map((a) => (a.id === id ? { ...a, locked: !a.locked } : a)));
  };

  const chartOption = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item", backgroundColor: "#1e293b", borderColor: "#334155",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: "{b}: {c}%",
    },
    series: [{
      type: "pie", radius: ["45%", "72%"], center: ["50%", "50%"],
      itemStyle: { borderColor: "#0f172a", borderWidth: 3 },
      label: { show: false },
      data: allocations.map((a) => ({ value: a.weight, name: a.name, itemStyle: { color: a.color } })),
    }],
  };

  if (loading) {
    return (
      <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col animate-pulse">
        <div className="flex-1 flex items-center justify-center">
          <div className="h-[200px] w-[200px] bg-slate-800/30 rounded-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <PieChart size={14} className="text-indigo-400" />
          <span className="text-xs font-semibold">资产配置</span>
        </div>
        <button
          onClick={() => toast("success", "资产配置已再平衡")}
          className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors"
        >
          再平衡
        </button>
      </div>

      <div className="px-4 py-2">
        <ReactECharts option={chartOption} style={{ height: 200 }} />
      </div>

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
            <div className="flex items-center gap-3">
              <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${a.weight}%`, backgroundColor: a.color }} />
              </div>
              <span className="text-sm font-bold font-mono w-10 text-right">{a.weight}%</span>
            </div>
            <div className="flex gap-3 mt-2 text-[10px] text-slate-500">
              <span>S: {a.sharpe.toFixed(2)}</span>
              <span>α: {a.alpha >= 0 ? "+" : ""}{a.alpha}%</span>
            </div>
          </div>
        ))}
      </div>

      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex justify-between text-[10px]">
          <span className="text-slate-500">合计</span>
          <span className="font-mono font-semibold">{allocations.reduce((s, a) => s + a.weight, 0)}%</span>
        </div>
      </div>
    </div>
  );
}
