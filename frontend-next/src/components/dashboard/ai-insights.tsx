"use client";

import { Sparkles, TrendingUp, Brain, Zap } from "lucide-react";

const insights = [
  {
    icon: Brain,
    title: "Alpha Factory 分析",
    text: "量价因子(V6F)连续90天Alpha>10%，是当前最稳定Alpha来源。建议增加资金配置。",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: TrendingUp,
    title: "市场信号",
    text: "近5日北向资金净流入+120亿，融资余额连续3天上升，市场情绪偏多。",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  {
    icon: Zap,
    title: "策略建议",
    text: "F5F基本面策略Alpha衰减中，建议将资金从13.2%降至8%，转移至V6F。",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
];

export default function AIInsights() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={14} className="text-violet-400" />
        <h3 className="text-sm font-semibold">AI Insights</h3>
      </div>

      <div className="space-y-3">
        {insights.map((item, idx) => (
          <div
            key={idx}
            className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 hover:border-slate-700 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-6 h-6 rounded-md ${item.bg} flex items-center justify-center`}>
                <item.icon size={12} className={item.color} />
              </div>
              <span className="text-xs font-medium">{item.title}</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">{item.text}</p>
          </div>
        ))}
      </div>

      {/* Quick stats */}
      <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-3 gap-3">
        <div className="text-center">
          <div className="text-lg font-bold font-mono text-emerald-400">88</div>
          <div className="text-[9px] text-slate-500">VALIDATED</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold font-mono text-blue-400">2.50</div>
          <div className="text-[9px] text-slate-500">BEST SHARPE</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold font-mono text-violet-400">+16.9%</div>
          <div className="text-[9px] text-slate-500">BEST ALPHA</div>
        </div>
      </div>
    </div>
  );
}
