"use client";

import { useEffect, useState } from "react";
import { Radio, TrendingUp, TrendingDown, BarChart3, Target, Shield } from "lucide-react";

interface SignalItem {
  rank: number;
  code: string;
  name: string;
  industry: string;
  score: number;
  price: number;
  change: number;
  high?: number;
  low?: number;
  pe?: number;
  market_cap?: number;
  target_weight?: number;
}

export default function SignalsPage() {
  const [signals, setSignals] = useState<SignalItem[]>([]);
  const [date, setDate] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/trading/signals")
      .then((r) => r.json())
      .then((d) => {
        if (d.signals) setSignals(d.signals);
        if (d.date) setDate(d.date);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const buySignals = signals;
  const avgScore = signals.length > 0
    ? signals.reduce((s, x) => s + x.score, 0) / signals.length
    : 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center">
          <Radio size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            信号追踪
          </h1>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            多因子选股信号 · 评分排序 · 动态权重 {date ? `· ${date}` : ""}
          </p>
        </div>
        {!loading && (
          <div className="ml-auto flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
            <span>选出 <strong style={{ color: "var(--accent)" }}>{signals.length}</strong> 只</span>
            <span>均分 <strong style={{ color: "var(--text-primary)" }}>{avgScore.toFixed(3)}</strong></span>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20" style={{ color: "var(--text-muted)" }}>
          <BarChart3 size={20} className="animate-pulse" />
        </div>
      ) : signals.length === 0 ? (
        <div
          className="rounded-xl p-12 text-center"
          style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}
        >
          <Radio size={32} className="mx-auto mb-3" style={{ color: "var(--text-muted)" }} />
          <p style={{ color: "var(--text-secondary)" }}>暂无信号</p>
          <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
            等待下一轮因子扫描
          </p>
        </div>
      ) : (
        <div className="grid gap-3">
          {buySignals.map((s) => (
            <div
              key={`${s.code}`}
              className="rounded-xl p-4 transition-all hover:border-opacity-50 flex items-center gap-4"
              style={{
                backgroundColor: "var(--bg-card)",
                border: "1px solid var(--border-color)",
              }}
            >
              {/* Rank */}
              <div className="w-9 h-9 rounded-lg flex items-center justify-center font-mono font-bold text-xs"
                style={{
                  backgroundColor: s.rank <= 3 ? "rgba(234,179,8,0.15)" : "rgba(255,255,255,0.05)",
                  color: s.rank <= 3 ? "#eab308" : "var(--text-muted)",
                }}>
                {s.rank}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                    {s.name}
                  </span>
                  <span className="text-[11px] px-1.5 py-0.5 rounded font-mono" style={{
                    color: "var(--text-muted)", backgroundColor: "rgba(255,255,255,0.05)",
                  }}>
                    {s.code}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded"
                    style={{ color: "var(--text-secondary)", backgroundColor: "rgba(59,130,246,0.1)" }}>
                    {s.industry || "--"}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1 text-[11px]">
                  <span className="font-mono" style={{ color: s.change > 0 ? "#22c55e" : "#ef4444" }}>
                    {s.change > 0 ? "+" : ""}{s.change}%
                  </span>
                  <span style={{ color: "var(--text-muted)" }}>
                    评分 <span className="font-mono" style={{ color: "var(--accent)" }}>{s.score.toFixed(3)}</span>
                  </span>
                  {s.pe && (
                    <span style={{ color: "var(--text-muted)" }}>
                      PE <span className="font-mono" style={{ color: "var(--text-secondary)" }}>{s.pe}</span>
                    </span>
                  )}
                  {s.market_cap && (
                    <span style={{ color: "var(--text-muted)" }}>
                      市值 <span className="font-mono" style={{ color: "var(--text-secondary)" }}>{s.market_cap}亿</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Right: price + weight */}
              <div className="flex items-center gap-4 text-right">
                <div>
                  <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>当前价</div>
                  <div className="font-mono font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                    {s.price.toFixed(2)}
                  </div>
                </div>
                {s.target_weight != null && (
                  <div className="w-14">
                    <div className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>权重</div>
                    <div className="h-1.5 rounded-full" style={{ backgroundColor: "rgba(255,255,255,0.08)" }}>
                      <div className="h-full rounded-full" style={{
                        width: `${s.target_weight}%`,
                        backgroundColor: s.target_weight > 15 ? "#22c55e" : s.target_weight > 8 ? "#3b82f6" : "#64748B",
                      }} />
                    </div>
                    <div className="text-[9px] font-mono mt-0.5" style={{ color: "var(--text-muted)" }}>
                      {s.target_weight.toFixed(1)}%
                    </div>
                  </div>
                )}
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${s.score > 0.05 ? "bg-emerald-500/10" : "bg-amber-500/10"}`}>
                  {s.score > 0.05 ? <TrendingUp size={15} color="#22c55e" /> : <Target size={15} color="#eab308" />}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
