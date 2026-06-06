"use client";

import { Zap, ArrowDownCircle, Pause, Bell, CheckCircle2, Clock } from "lucide-react";

const actions = [
  {
    id: 1,
    type: "reduce",
    icon: ArrowDownCircle,
    label: "Reduce Position",
    target: "MF V25 → 30%",
    reason: "Concentration risk 40% > threshold",
    status: "pending",
    time: "Pending",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20",
  },
  {
    id: 2,
    type: "pause",
    icon: Pause,
    label: "Pause Strategy",
    target: "Breakout V3",
    reason: "Alpha decay detected",
    status: "executed",
    time: "2h ago",
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/20",
  },
  {
    id: 3,
    type: "notify",
    icon: Bell,
    label: "Notify",
    target: "All Active",
    reason: "VIX spike > 20%",
    status: "standby",
    time: "Standby",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20",
  },
];

export default function AutoActions() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Zap size={14} className="text-amber-400" />
        <span className="text-xs font-semibold">Auto Actions</span>
        <span className="text-[10px] text-slate-500 ml-auto">Rule Engine</span>
      </div>

      <div className="space-y-2">
        {actions.map((action) => (
          <div
            key={action.id}
            className={`p-3 rounded-lg border ${action.bgColor} ${action.borderColor}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <action.icon size={12} className={action.color} />
              <span className={`text-xs font-medium ${action.color}`}>{action.label}</span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded ml-auto ${
                action.status === "executed"
                  ? "bg-emerald-500/10 text-emerald-400"
                  : action.status === "pending"
                  ? "bg-amber-500/10 text-amber-400"
                  : "bg-slate-500/10 text-slate-400"
              }`}>
                {action.status}
              </span>
            </div>
            <div className="text-[10px] text-slate-400">{action.target}</div>
            <div className="text-[9px] text-slate-500 mt-1 flex items-center gap-1">
              <Clock size={8} />
              {action.reason} · {action.time}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
