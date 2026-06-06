"use client";

import { AlertTriangle, Info, XCircle, Shield } from "lucide-react";

const alerts = [
  {
    level: "critical",
    icon: XCircle,
    title: "FF4F Alpha Dead",
    desc: "Alpha 转负: 30d=-2.0%, 60d=-2.0%, 已自动标记 RETIRED",
    time: "10分钟前",
  },
  {
    level: "warning",
    icon: AlertTriangle,
    title: "F5F Alpha Degrading",
    desc: "30d Alpha (7.4%) < 60d×0.7 (6.3%), 已移入 WATCHLIST",
    time: "1小时前",
  },
  {
    level: "info",
    icon: Info,
    title: "DD Control Normal",
    desc: "当前回撤 1.25%, 远低于 Level 1 阈值 (10%)",
    time: "持续监控中",
  },
];

const levelStyles: Record<string, { bg: string; border: string; icon: string }> = {
  critical: {
    bg: "bg-red-500/5",
    border: "border-red-500/20",
    icon: "text-red-400",
  },
  warning: {
    bg: "bg-amber-500/5",
    border: "border-amber-500/20",
    icon: "text-amber-400",
  },
  info: {
    bg: "bg-blue-500/5",
    border: "border-blue-500/20",
    icon: "text-blue-400",
  },
};

export default function RiskAlert() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Shield size={14} className="text-slate-400" />
        <h3 className="text-sm font-semibold">风险告警</h3>
      </div>

      <div className="space-y-2">
        {alerts.map((a, idx) => {
          const style = levelStyles[a.level];
          return (
            <div
              key={idx}
              className={`flex items-start gap-3 p-3 rounded-lg border ${style.bg} ${style.border}`}
            >
              <a.icon size={16} className={`${style.icon} mt-0.5 flex-shrink-0`} />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium">{a.title}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">{a.desc}</div>
              </div>
              <span className="text-[10px] text-slate-600 flex-shrink-0">{a.time}</span>
            </div>
          );
        })}
      </div>

      {/* Drawdown Control Bar */}
      <div className="mt-5 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-slate-400">回撤控制</span>
          <span className="text-xs font-mono text-emerald-400">1.25%</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full transition-all duration-500"
            style={{ width: "6.25%" }}
          />
        </div>
        <div className="flex justify-between mt-1.5">
          <span className="text-[9px] text-slate-600">0%</span>
          <span className="text-[9px] text-slate-600">NORMAL</span>
          <span className="text-[9px] text-amber-600">10%</span>
          <span className="text-[9px] text-amber-600">15%</span>
          <span className="text-[9px] text-red-600">20%</span>
        </div>
      </div>
    </div>
  );
}
