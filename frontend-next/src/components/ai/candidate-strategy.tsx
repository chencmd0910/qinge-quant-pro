"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Play, ChevronDown, ChevronUp, Target, Activity } from "lucide-react";
import api from "@/lib/axios";
import { toast } from "@/lib/toast";

interface Candidate {
  id: string;
  name: string;
  annual: number;
  sharpe: number;
  alpha: number;
  maxDD: number;
  trades: number;
  winRate: number;
  status: string;
}

const statusColors: Record<string, string> = {
  "VALIDATED": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  "VALIDATING": "bg-amber-500/10 text-amber-400 border-amber-500/20",
  "DRAFT": "bg-slate-500/10 text-slate-400 border-slate-500/20",
};

export default function CandidateStrategy() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    api.get("/api/strategy-lab/results")
      .then(({ data }) => setCandidates(data.results || []))
      .catch(() => {});
  }, []);

  if (!candidates.length) {
    return (
      <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-center">
        <span className="text-xs text-slate-500">暂无候选策略</span>
      </div>
    );
  }

  const bestShp = Math.max(...candidates.map(c => c.sharpe));
  const bestAlpha = Math.max(...candidates.map(c => c.alpha));

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-emerald-500/10 flex items-center justify-center">
            <Target size={12} className="text-emerald-400" />
          </div>
          <div>
            <div className="text-xs font-semibold">策略候选</div>
            <div className="text-[9px] text-slate-500">{candidates.length} 个策略</div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-3 space-y-2">
        {candidates.map((s) => (
          <div
            key={s.id} className="rounded-lg bg-slate-800/40 border border-slate-700/30 hover:border-slate-600/50 transition-colors"
          >
            <div className="p-3 cursor-pointer" onClick={() => setExpanded(expanded === s.id ? null : s.id)}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Activity size={12} className="text-blue-400" />
                  <span className="text-xs font-medium">{s.name}</span>
                </div>
                <div className={`text-[9px] px-1.5 py-0.5 rounded border ${statusColors[s.status] || statusColors["DRAFT"]}`}>
                  {s.status}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <div className="text-[9px] text-slate-500">夏普</div>
                  <div className="text-xs font-mono font-semibold text-emerald-400">{s.sharpe.toFixed(3)}</div>
                </div>
                <div>
                  <div className="text-[9px] text-slate-500">Alpha</div>
                  <div className="text-xs font-mono font-semibold text-emerald-400">{s.alpha >= 0 ? "+" : ""}{s.alpha}%</div>
                </div>
                <div>
                  <div className="text-[9px] text-slate-500">胜率</div>
                  <div className="text-xs font-mono font-semibold">{s.winRate}%</div>
                </div>
              </div>

              <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-1">
                  {s.annual > 0 ? <TrendingUp size={10} className="text-emerald-400" /> : <TrendingDown size={10} className="text-red-400" />}
                  <span className={`text-[10px] font-mono ${s.annual > 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {s.annual > 0 ? "+" : ""}{s.annual}%
                  </span>
                </div>
                {expanded === s.id ? <ChevronUp size={12} className="text-slate-500" /> : <ChevronDown size={12} className="text-slate-500" />}
              </div>
            </div>

            {expanded === s.id && (
              <div className="px-3 pb-3 border-t border-slate-700/30 pt-2">
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="p-2 rounded bg-slate-700/30">
                    <div className="text-[9px] text-slate-500">年化收益</div>
                    <div className="text-xs font-mono font-semibold text-emerald-400">+{s.annual}%</div>
                  </div>
                  <div className="p-2 rounded bg-slate-700/30">
                    <div className="text-[9px] text-slate-500">最大回撤</div>
                    <div className="text-xs font-mono font-semibold text-red-400">{s.maxDD}%</div>
                  </div>
                  <div className="p-2 rounded bg-slate-700/30">
                    <div className="text-[9px] text-slate-500">交易笔数</div>
                    <div className="text-xs font-mono font-semibold">{s.trades}</div>
                  </div>
                  <div className="p-2 rounded bg-slate-700/30">
                    <div className="text-[9px] text-slate-500">胜率</div>
                    <div className="text-xs font-mono font-semibold text-emerald-400">{s.winRate}%</div>
                  </div>
                </div>

                <button
                  onClick={() => toast("info", `${s.name} 已添加到回测队列`)}
                  className="w-full h-8 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Play size={12} />
                  <span className="text-xs font-medium">一键回测</span>
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="px-4 py-3 border-t border-slate-800">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="text-sm font-bold font-mono text-emerald-400">{candidates.length}</div>
            <div className="text-[8px] text-slate-500">候选策略</div>
          </div>
          <div>
            <div className="text-sm font-bold font-mono text-blue-400">{bestShp.toFixed(2)}</div>
            <div className="text-[8px] text-slate-500">最佳夏普</div>
          </div>
          <div>
            <div className="text-sm font-bold font-mono text-violet-400">{bestAlpha >= 0 ? "+" : ""}{bestAlpha}%</div>
            <div className="text-[8px] text-slate-500">最佳 Alpha</div>
          </div>
        </div>
      </div>
    </div>
  );
}
