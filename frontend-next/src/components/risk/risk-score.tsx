"use client";

import { Shield } from "lucide-react";

export default function RiskScore() {
  const score = 82;
  const maxScore = 100;

  // Calculate angle for gauge
  const angle = (score / maxScore) * 180;
  const startAngle = 180;
  const endAngle = startAngle + angle;

  const getColor = (s: number) => {
    if (s >= 80) return "#22c55e";
    if (s >= 60) return "#eab308";
    if (s >= 40) return "#f97316";
    return "#ef4444";
  };

  const getLabel = (s: number) => {
    if (s >= 80) return "LOW RISK";
    if (s >= 60) return "MODERATE";
    if (s >= 40) return "ELEVATED";
    return "HIGH RISK";
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Shield size={14} className="text-emerald-400" />
        <span className="text-xs font-semibold">Risk Score</span>
      </div>

      <div className="flex flex-col items-center">
        {/* Gauge */}
        <div className="relative w-48 h-24 mb-4">
          <svg viewBox="0 0 200 100" className="w-full h-full">
            {/* Background arc */}
            <path
              d="M 10 95 A 90 90 0 0 1 190 95"
              fill="none"
              stroke="#1e293b"
              strokeWidth="12"
              strokeLinecap="round"
            />
            {/* Score arc */}
            <path
              d="M 10 95 A 90 90 0 0 1 190 95"
              fill="none"
              stroke={getColor(score)}
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${(score / 100) * 283} 283`}
              className="transition-all duration-1000"
            />
            {/* Center text */}
            <text
              x="100"
              y="75"
              textAnchor="middle"
              className="text-3xl font-bold"
              fill="#e2e8f0"
              fontSize="32"
              fontFamily="monospace"
            >
              {score}
            </text>
            <text
              x="100"
              y="95"
              textAnchor="middle"
              fill={getColor(score)}
              fontSize="10"
              fontWeight="600"
            >
              {getLabel(score)}
            </text>
          </svg>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-3 w-full">
          <div className="text-center p-2 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Market</div>
            <div className="text-sm font-bold font-mono text-emerald-400">85</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Strategy</div>
            <div className="text-sm font-bold font-mono text-emerald-400">80</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-slate-800/60">
            <div className="text-[9px] text-slate-500">Portfolio</div>
            <div className="text-sm font-bold font-mono text-amber-400">78</div>
          </div>
        </div>
      </div>
    </div>
  );
}
