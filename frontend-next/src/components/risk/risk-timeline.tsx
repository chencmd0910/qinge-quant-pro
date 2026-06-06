"use client";

import { Clock, AlertTriangle, CheckCircle2, Bell } from "lucide-react";

const events = [
  { time: "14:32", type: "info", message: "Risk score updated: 82/100" },
  { time: "14:15", type: "warn", message: "MF V25 concentration 40%" },
  { time: "13:45", type: "ok", message: "VIX returned to normal range" },
  { time: "12:20", type: "alert", message: "Breakout V3 alpha decay" },
  { time: "11:00", type: "ok", message: "All strategies within limits" },
  { time: "10:30", type: "info", message: "Morning risk check passed" },
  { time: "09:30", type: "info", message: "Market open - risk monitor active" },
];

const typeIcons: Record<string, any> = {
  info: Bell,
  warn: AlertTriangle,
  ok: CheckCircle2,
  alert: AlertTriangle,
};

const typeColors: Record<string, string> = {
  info: "text-blue-400",
  warn: "text-amber-400",
  ok: "text-emerald-400",
  alert: "text-red-400",
};

export default function RiskTimeline() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Clock size={14} className="text-slate-400" />
        <span className="text-xs font-semibold">Risk Timeline</span>
      </div>

      <div className="space-y-2 max-h-[200px] overflow-auto">
        {events.map((event, idx) => {
          const Icon = typeIcons[event.type];
          return (
            <div key={idx} className="flex items-start gap-2 py-1.5">
              <div className="text-[10px] text-slate-600 w-10 flex-shrink-0 pt-0.5">{event.time}</div>
              <Icon size={12} className={`${typeColors[event.type]} mt-0.5 flex-shrink-0`} />
              <span className="text-[11px] text-slate-400">{event.message}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
