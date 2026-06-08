"use client";

import { useEffect, useState } from "react";
import { Clock, AlertTriangle, CheckCircle2, Bell } from "lucide-react";
import api from "@/lib/axios";

interface Event {
  time: string;
  type: string;
  message: string;
}

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
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    api.get("/api/risk/timeline")
      .then(({ data }) => setEvents(data.events || []))
      .catch(() => {});
  }, []);

  if (!events.length) return null;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Clock size={14} className="text-slate-400" />
        <span className="text-xs font-semibold">风险时间线</span>
      </div>

      <div className="space-y-2 max-h-[200px] overflow-auto">
        {events.map((event, idx) => {
          const Icon = typeIcons[event.type] || Bell;
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
