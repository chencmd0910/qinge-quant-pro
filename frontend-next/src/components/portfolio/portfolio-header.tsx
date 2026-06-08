"use client";

import { PieChart, Settings, RefreshCw } from "lucide-react";
import { toast } from "@/lib/toast";

export default function PortfolioHeader() {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
          <PieChart size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold">投资组合</h1>
          <p className="text-xs text-slate-500">策略配置与风险管理</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            toast("success", "配置已刷新");
            window.location.reload();
          }}
          className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors"
        >
          <RefreshCw size={14} className="text-slate-400" />
        </button>
        <button
          onClick={() => toast("info", "设置面板暂未开放")}
          className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors"
        >
          <Settings size={14} className="text-slate-400" />
        </button>
      </div>
    </div>
  );
}
