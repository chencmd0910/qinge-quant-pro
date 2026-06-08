"use client";

import { useEffect, useState } from "react";
import { Shield } from "lucide-react";
import api from "@/lib/axios";

export default function RiskScore() {
  const [score, setScore] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/dashboard/summary")
      .then(({ data }) => {
        // 综合风险评分: 夏普占比50%, 回撤占比30%, 胜率占比20%
        const sharpe = Math.min((data.sharpe_ratio ?? 0) / 2.5, 1) * 50;
        const drawdown = Math.max(1 - (data.max_drawdown ?? 0) / 25, 0) * 30;
        const winRate = ((data.win_rate ?? 0) / 100) * 20;
        setScore(Math.round(sharpe + drawdown + winRate));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading || score === null) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 animate-pulse">
        <div className="h-4 w-20 bg-slate-800 rounded mb-4" />
        <div className="flex flex-col items-center">
          <div className="w-48 h-24 bg-slate-800/50 rounded-full" />
          <div className="h-8 w-28 bg-slate-800 rounded mt-2" />
        </div>
      </div>
    );
  }

  const getColor = (s: number) => {
    if (s >= 80) return "#22c55e";
    if (s >= 60) return "#eab308";
    if (s >= 40) return "#f97316";
    return "#ef4444";
  };

  const getLabel = (s: number) => {
    if (s >= 80) return "低风险";
    if (s >= 60) return "中等";
    if (s >= 40) return "偏高";
    return "高风险";
  };

  const color = getColor(score);
  const label = getLabel(score);

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Shield size={14} className="text-emerald-400" />
        <span className="text-xs font-semibold">风险评分</span>
      </div>

      <div className="flex flex-col items-center">
        {/* Simple gauge */}
        <div className="relative w-48 h-24 mb-4">
          <svg viewBox="0 0 200 100" className="w-full h-full">
            <path
              d="M 20 90 A 80 80 0 0 1 180 90"
              fill="none"
              stroke="#1e293b"
              strokeWidth="12"
              strokeLinecap="round"
            />
            <path
              d="M 20 90 A 80 80 0 0 1 180 90"
              fill="none"
              stroke={color}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${(score / 100) * 251} 251`}
            />
            {/* Needle */}
            <line
              x1="100" y1="90"
              x2={100 + 70 * Math.cos(Math.PI - (score / 100) * Math.PI)}
              y2={90 - 70 * Math.sin(Math.PI - (score / 100) * Math.PI)}
              stroke="#e2e8f0"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <circle cx="100" cy="90" r="3" fill="#e2e8f0" />
          </svg>
        </div>

        <div className="text-3xl font-bold font-mono" style={{ color }}>
          {score}
        </div>
        <div className="text-xs mt-1 px-3 py-0.5 rounded-full font-medium" style={{
          backgroundColor: `${color}15`,
          color,
          border: `1px solid ${color}30`,
        }}>
          {label}
        </div>
      </div>
    </div>
  );
}
