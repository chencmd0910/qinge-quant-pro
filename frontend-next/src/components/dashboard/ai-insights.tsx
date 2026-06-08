"use client";

import { useEffect, useState } from "react";
import { Sparkles, TrendingUp, Brain, Zap, Lightbulb } from "lucide-react";
import api from "@/lib/axios";

interface Insight {
  title: string;
  body: string;
  tag: string;
  tag_color: string;
}

const iconMap: Record<string, any> = {
  "绩效": TrendingUp,
  "策略": Brain,
  "因子": Lightbulb,
  "信号": Zap,
};

export default function AIInsights() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/dashboard/summary")
      .then(({ data }) => {
        if (data.insights?.length) {
          setInsights(data.insights);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl p-5 animate-pulse" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
        <div className="h-4 w-20 bg-slate-800 rounded mb-4" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="mb-3">
            <div className="h-3 w-40 bg-slate-800 rounded mb-1" />
            <div className="h-6 w-full bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (!insights.length) return null;

  return (
    <div className="rounded-xl p-5" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={14} className="text-violet-400" />
        <h3 className="text-sm font-semibold">AI 洞察</h3>
      </div>

      <div className="space-y-3">
        {insights.map((item, idx) => {
          const Icon = iconMap[item.tag] || Brain;
          return (
            <div
              key={idx}
              className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30 hover:border-slate-600/50 transition-colors"
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon size={12} className={item.tag_color || "text-blue-400"} />
                <span className="text-xs font-medium">{item.title}</span>
                {item.tag && (
                  <span className={`text-[9px] px-1.5 py-0.5 rounded ml-auto ${item.tag_color?.replace("text-", "bg-").replace("400", "500/10")} ${item.tag_color}`}>
                    {item.tag}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">{item.body}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
