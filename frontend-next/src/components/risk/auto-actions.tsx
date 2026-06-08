"use client";

import { useEffect, useState } from "react";
import { Zap, ArrowDownCircle, Pause, Bell, Clock, CheckCircle2 } from "lucide-react";
import api from "@/lib/axios";

interface Action {
  id: number;
  type: string;
  label: string;
  target: string;
  reason: string;
  status: string;
}

const typeIcons: Record<string, any> = {
  reduce: ArrowDownCircle,
  pause: Pause,
  notify: Bell,
};

const typeColors: Record<string, { color: string; bg: string; border: string }> = {
  reduce: { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  pause: { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" },
  notify: { color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
};

export default function AutoActions() {
  const [actions, setActions] = useState<Action[]>([]);

  useEffect(() => {
    api.get("/api/risk/auto-actions")
      .then(({ data }) => setActions(data.actions || []))
      .catch(() => {});
  }, []);

  if (!actions.length) return null;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Zap size={14} className="text-amber-400" />
        <span className="text-xs font-semibold">自动操作</span>
        <span className="text-[10px] text-slate-500 ml-auto">规则引擎</span>
      </div>

      <div className="space-y-2">
        {actions.map((action) => {
          const Icon = typeIcons[action.type] || Bell;
          const tc = typeColors[action.type] || typeColors.notify;
          return (
            <div key={action.id} className={`p-3 rounded-lg border ${tc.bg} ${tc.border}`}>
              <div className="flex items-center gap-2 mb-1">
                <Icon size={12} className={tc.color} />
                <span className={`text-xs font-medium ${tc.color}`}>{action.label}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded ml-auto ${
                  action.status === "已执行" ? "bg-emerald-500/10 text-emerald-400"
                  : action.status === "待执行" ? "bg-amber-500/10 text-amber-400"
                  : "bg-emerald-500/10 text-emerald-400"
                }`}>
                  {action.status}
                </span>
              </div>
              <div className="text-[10px] text-slate-400">{action.target}</div>
              <div className="text-[9px] text-slate-500 mt-1 flex items-center gap-1">
                <Clock size={8} />
                {action.reason}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
