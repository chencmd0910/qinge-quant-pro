"use client";

import { useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Play,
  ChevronDown,
  ChevronUp,
  Zap,
  Target,
  Activity,
} from "lucide-react";

const candidates = [
  {
    id: "AUTO_0023_a8f3c1",
    name: "量价_6F_biweekly",
    cluster: "Volume/Price",
    annual: 19.57,
    sharpe: 2.5,
    alpha: 16.9,
    maxDD: -5.0,
    score: 91.0,
    factors: ["volume_ratio", "money_flow", "mom_5d", "mom_10d", "volatility_20d", "daily_sharpe"],
    status: "VALIDATED",
  },
  {
    id: "AUTO_0047_b2d9e4",
    name: "基本面_5F_biweekly",
    cluster: "Fundamental",
    annual: 15.04,
    sharpe: 1.594,
    alpha: 12.6,
    maxDD: -13.46,
    score: 75.4,
    factors: ["pe_ttm", "pb_ttm", "industry_revenue_growth", "industry_profit_growth", "industry_pmi"],
    status: "VALIDATED",
  },
  {
    id: "AUTO_0061_c4e7f2",
    name: "动量_5F_weekly",
    cluster: "Momentum",
    annual: 11.06,
    sharpe: 1.612,
    alpha: 10.1,
    maxDD: -10.09,
    score: 72.4,
    factors: ["mom_5d", "mom_10d", "consistency", "mom_20d", "volume_ratio"],
    status: "VALIDATED",
  },
  {
    id: "AUTO_0088_d1a5b7",
    name: "资金流_4F_biweekly",
    cluster: "Fund Flow",
    annual: 11.73,
    sharpe: 1.704,
    alpha: 11.0,
    maxDD: -9.73,
    score: 75.3,
    factors: ["money_flow", "northbound_net_buy", "margin_balance_chg", "volume_ratio"],
    status: "VALIDATED",
  },
  {
    id: "AUTO_0095_e3f8a1",
    name: "北向_4F_biweekly",
    cluster: "Northbound",
    annual: 10.5,
    sharpe: 1.5,
    alpha: 8.2,
    maxDD: -8.5,
    score: 68.0,
    factors: ["northbound_net_buy", "northbound_holding_chg", "margin_balance_chg", "volume_ratio"],
    status: "VALIDATED",
  },
];

const statusColors: Record<string, string> = {
  VALIDATED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  BACKTESTED: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  FILTERED: "bg-red-500/10 text-red-400 border-red-500/20",
};

export default function CandidateStrategy() {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-emerald-500/10 flex items-center justify-center">
            <Target size={12} className="text-emerald-400" />
          </div>
          <div>
            <div className="text-xs font-semibold">Candidates</div>
            <div className="text-[9px] text-slate-500">{candidates.length} strategies</div>
          </div>
        </div>
      </div>

      {/* Strategy list */}
      <div className="flex-1 overflow-auto p-3 space-y-2">
        {candidates.map((s) => (
          <div
            key={s.id}
            className="rounded-lg bg-slate-800/40 border border-slate-700/30 hover:border-slate-600/50 transition-colors"
          >
            {/* Main info */}
            <div
              className="p-3 cursor-pointer"
              onClick={() => setExpanded(expanded === s.id ? null : s.id)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Activity size={12} className="text-blue-400" />
                  <span className="text-xs font-medium">{s.name}</span>
                </div>
                <div className={`text-[9px] px-1.5 py-0.5 rounded border ${statusColors[s.status]}`}>
                  {s.status}
                </div>
              </div>

              <div className="text-[10px] text-slate-500 mb-2">{s.cluster}</div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <div className="text-[9px] text-slate-500">Sharpe</div>
                  <div className="text-xs font-mono font-semibold text-emerald-400">
                    {s.sharpe.toFixed(3)}
                  </div>
                </div>
                <div>
                  <div className="text-[9px] text-slate-500">Alpha</div>
                  <div className="text-xs font-mono font-semibold text-emerald-400">
                    +{s.alpha}%
                  </div>
                </div>
                <div>
                  <div className="text-[9px] text-slate-500">Score</div>
                  <div className="text-xs font-mono font-semibold">{s.score}</div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-1">
                  {s.annual > 0 ? (
                    <TrendingUp size={10} className="text-emerald-400" />
                  ) : (
                    <TrendingDown size={10} className="text-red-400" />
                  )}
                  <span className={`text-[10px] font-mono ${
                    s.annual > 0 ? "text-emerald-400" : "text-red-400"
                  }`}>
                    {s.annual > 0 ? "+" : ""}{s.annual}%
                  </span>
                </div>
                {expanded === s.id ? (
                  <ChevronUp size={12} className="text-slate-500" />
                ) : (
                  <ChevronDown size={12} className="text-slate-500" />
                )}
              </div>
            </div>

            {/* Expanded details */}
            {expanded === s.id && (
              <div className="px-3 pb-3 border-t border-slate-700/30 pt-2">
                <div className="text-[9px] text-slate-500 mb-1.5">Factors</div>
                <div className="flex flex-wrap gap-1 mb-3">
                  {s.factors.map((f) => (
                    <span
                      key={f}
                      className="px-2 py-0.5 text-[9px] bg-slate-700/50 text-slate-400 rounded"
                    >
                      {f}
                    </span>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="p-2 rounded bg-slate-700/30">
                    <div className="text-[9px] text-slate-500">Annual</div>
                    <div className="text-xs font-mono font-semibold text-emerald-400">
                      +{s.annual}%
                    </div>
                  </div>
                  <div className="p-2 rounded bg-slate-700/30">
                    <div className="text-[9px] text-slate-500">Max DD</div>
                    <div className="text-xs font-mono font-semibold text-red-400">
                      {s.maxDD}%
                    </div>
                  </div>
                </div>

                <button className="w-full h-8 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center gap-1.5 transition-colors">
                  <Play size={12} />
                  <span className="text-xs font-medium">一键回测</span>
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer stats */}
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="text-sm font-bold font-mono text-emerald-400">88</div>
            <div className="text-[8px] text-slate-500">VALIDATED</div>
          </div>
          <div>
            <div className="text-sm font-bold font-mono text-blue-400">2.50</div>
            <div className="text-[8px] text-slate-500">BEST SHARPE</div>
          </div>
          <div>
            <div className="text-sm font-bold font-mono text-violet-400">+16.9%</div>
            <div className="text-[8px] text-slate-500">BEST ALPHA</div>
          </div>
        </div>
      </div>
    </div>
  );
}
