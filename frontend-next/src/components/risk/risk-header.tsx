"use client";

import { Shield, Bell, RefreshCw } from "lucide-react";
import { toast } from "@/lib/toast";

export default function RiskHeader() {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
          <Shield size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold">风险中心</h1>
          <p className="text-xs text-slate-500">实时风险监控与自动操作</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <div className="w-2 h-2 bg-emerald-400 rounded-full" />
          <span className="text-xs text-emerald-400">一切正常</span>
        </div>
        <button
          onClick={() => toast("info", "暂无新告警通知")}
          className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors relative"
        >
          <Bell size={14} className="text-slate-400" />
        </button>
        <button
          onClick={() => toast("success", "风险数据已刷新")}
          className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-colors"
        >
          <RefreshCw size={14} className="text-slate-400" />
        </button>
      </div>
    </div>
  );
}
