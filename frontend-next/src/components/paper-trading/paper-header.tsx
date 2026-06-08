"use client";

import { useState } from "react";
import { CandlestickChart, Play, Pause, RotateCcw, Settings, SkipForward } from "lucide-react";
import api from "@/lib/axios";
import { toast } from "@/lib/toast";

interface PaperHeaderProps {
  onRefresh: () => void;
}

export default function PaperHeader({ onRefresh }: PaperHeaderProps) {
  const [running, setRunning] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleDailyUpdate = async () => {
    setLoading(true);
    try {
      const { data } = await api.post("/api/paper-trading/daily-update");
      toast("success", `模拟推进 1 天 → ${data.date}，净值 ¥${data.total_value.toLocaleString()}`);
      onRefresh();
    } catch {
      toast("error", "每日推进失败");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      const { data } = await api.post("/api/paper-trading/reset");
      toast("info", data.message || "模拟交易已重置");
      onRefresh();
    } catch {
      toast("error", "重置失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
          <CandlestickChart size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold">模拟交易</h1>
          <p className="text-xs text-slate-500">每日推进模拟 · 策略信号驱动交易</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Daily advance button */}
        <button
          onClick={handleDailyUpdate}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 disabled:opacity-40 transition-all"
        >
          <SkipForward size={12} />
          <span className="text-xs font-medium">{loading ? "推进中..." : "每日推进"}</span>
        </button>

        {/* Pause/Resume */}
        <button
          onClick={() => {
            setRunning(!running);
            toast(running ? "info" : "success", running ? "模拟交易已暂停" : "模拟交易已恢复");
          }}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors ${
            running
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : "bg-amber-500/10 border-amber-500/20 text-amber-400"
          }`}
        >
          {running ? <Play size={12} /> : <Pause size={12} />}
          <span className="text-xs">{running ? "运行中" : "已暂停"}</span>
        </button>

        {/* Reset */}
        <button
          onClick={handleReset}
          disabled={loading}
          className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 disabled:opacity-40 transition-colors"
          title="重置模拟交易"
        >
          <RotateCcw size={14} className="text-slate-400" />
        </button>

        {/* Settings */}
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
