"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Info, XCircle, Shield } from "lucide-react";
import api from "@/lib/axios";

interface AlertItem {
  level: string;
  title: string;
  desc: string;
  time: string;
}

const levelIcons: Record<string, any> = {
  critical: XCircle,
  warning: AlertTriangle,
  info: Info,
};

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
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [ddValue, setDdValue] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/dashboard/summary")
      .then(({ data }) => {
        if (data.alerts?.length) {
          setAlerts(data.alerts);
        }
        setDdValue(data.max_drawdown ?? 0);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 animate-pulse">
        <div className="h-4 w-20 bg-slate-800 rounded mb-4" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 bg-slate-800/20 rounded-lg mb-2" />
        ))}
      </div>
    );
  }

  // 回撤进度条百分比: ddValue 是最大回撤%，映射到 0-25% 范围
  const ddPct = Math.min(Math.max(ddValue, 0), 25);
  const ddWidth = (ddPct / 25) * 100;

  let ddLevel = "NORMAL";
  let ddColor = "emerald";
  if (ddValue > 20) { ddLevel = "危险"; ddColor = "red"; }
  else if (ddValue > 15) { ddLevel = "警告"; ddColor = "amber"; }
  else if (ddValue > 10) { ddLevel = "注意"; ddColor = "amber"; }
  else { ddLevel = "正常"; }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Shield size={14} className="text-slate-400" />
        <h3 className="text-sm font-semibold">风险告警</h3>
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-6 text-slate-500 text-xs">
          ✅ 暂无风险告警
        </div>
      ) : (
        <div className="space-y-2">
          {alerts.map((a, idx) => {
            const style = levelStyles[a.level] ?? levelStyles.info;
            const Icon = levelIcons[a.level] ?? Info;
            return (
              <div
                key={idx}
                className={`flex items-start gap-3 p-3 rounded-lg border ${style.bg} ${style.border}`}
              >
                <Icon size={16} className={`${style.icon} mt-0.5 flex-shrink-0`} />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium">{a.title}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{a.desc}</div>
                </div>
                <span className="text-[10px] text-slate-600 flex-shrink-0">{a.time}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Drawdown Control Bar */}
      <div className="mt-5 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-slate-400">回撤控制</span>
          <span className={`text-xs font-mono text-${ddColor}-400`}>{ddValue.toFixed(2)}%</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full bg-gradient-to-r from-${ddColor}-500 to-${ddColor}-400 rounded-full transition-all duration-500`}
            style={{ width: `${ddWidth}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5">
          <span className="text-[9px] text-slate-600">0%</span>
          <span className={`text-[9px] text-${ddColor}-600`}>{ddLevel}</span>
          <span className="text-[9px] text-amber-600">10%</span>
          <span className="text-[9px] text-amber-600">15%</span>
          <span className="text-[9px] text-red-600">20%</span>
        </div>
      </div>
    </div>
  );
}
