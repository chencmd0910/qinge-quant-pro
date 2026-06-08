"use client";

import { Factory } from "lucide-react";

export default function FactoryHeader({
  activeCount,
  watchCount,
  retiredCount,
}: {
  activeCount: number;
  watchCount: number;
  retiredCount: number;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
          <Factory size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold">Alpha 工厂</h1>
          <p className="text-xs text-slate-500">策略生命周期管理</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-blue-400 rounded-full" />
            <span className="text-slate-400">{activeCount} 活跃</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-amber-400 rounded-full" />
            <span className="text-slate-400">{watchCount} 观察</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-red-400 rounded-full" />
            <span className="text-slate-400">{retiredCount} 退役</span>
          </div>
        </div>
      </div>
    </div>
  );
}
