"use client";

import { useEffect, useState } from "react";
import { Shield, AlertTriangle, CheckCircle2, PieChart } from "lucide-react";
import ReactECharts from "echarts-for-react";

interface IndustryData {
  date: string;
  holdings: number;
  total_holdings: number;
  unique_industries: number;
  industry_limit: number;
  compliant: boolean;
  industry_counts: Record<string, number>;
  violations?: Array<{ industry: string; count: number; limit: number }>;
}

export default function IndustryCompliance() {
  const [data, setData] = useState<IndustryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v25/industry-breakdown")
      .then(r => r.json())
      .then(d => { if (d.date) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl p-4 animate-pulse" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
        <div className="h-4 w-32 rounded mb-4" style={{ background: "var(--border-color)" }} />
        <div className="h-40 rounded" style={{ background: "var(--border-color)", opacity: 0.3 }} />
      </div>
    );
  }

  if (!data) return null;

  const sorted = Object.entries(data.industry_counts || {})
    .sort((a, b) => b[1] - a[1]);

  const pieOpt = {
    tooltip: {
      trigger: "item",
      backgroundColor: "#1e293b",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: "{b}: {c}只 ({d}%)",
    },
    series: [{
      type: "pie",
      radius: ["40%", "75%"],
      center: ["50%", "50%"],
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 11, fontWeight: "bold" } },
      data: sorted.slice(0, 12).map(([name, count]) => ({
        name,
        value: count,
        itemStyle: {
          color: count > data.industry_limit * 0.8
            ? "rgba(239,68,68,0.7)"
            : count > data.industry_limit * 0.5
            ? "rgba(245,158,11,0.6)"
            : `hsla(${(sorted.indexOf([name, count]) * 40) % 360}, 60%, 50%, 0.6)`,
        },
      })),
    }],
  };

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Shield size={14} style={{ color: data.compliant ? "#22c55e" : "#ef4444" }} />
          <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
            行业合规监控
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          {data.compliant ? (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded" style={{ color: "#22c55e", backgroundColor: "rgba(34,197,94,0.1)" }}>
              <CheckCircle2 size={10} /> 合规
            </span>
          ) : (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded" style={{ color: "#ef4444", backgroundColor: "rgba(239,68,68,0.1)" }}>
              <AlertTriangle size={10} /> 超标
            </span>
          )}
          <span style={{ color: "var(--text-muted)" }}>{data.date}</span>
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="p-2 rounded text-center" style={{ backgroundColor: "rgba(255,255,255,0.03)" }}>
          <div className="text-lg font-bold font-mono" style={{ color: "var(--text-primary)" }}>{data.holdings}</div>
          <div className="text-[9px]" style={{ color: "var(--text-muted)" }}>持仓标的</div>
        </div>
        <div className="p-2 rounded text-center" style={{ backgroundColor: "rgba(255,255,255,0.03)" }}>
          <div className="text-lg font-bold font-mono" style={{ color: "var(--accent-blue)" }}>{data.unique_industries}</div>
          <div className="text-[9px]" style={{ color: "var(--text-muted)" }}>覆盖行业</div>
        </div>
        <div className="p-2 rounded text-center" style={{ backgroundColor: "rgba(255,255,255,0.03)" }}>
          <div className="text-lg font-bold font-mono" style={{ color: "var(--text-muted)" }}>{data.industry_limit}%</div>
          <div className="text-[9px]" style={{ color: "var(--text-muted)" }}>单行业上限</div>
        </div>
      </div>

      {/* Violations */}
      {data.violations && data.violations.length > 0 && (
        <div className="mb-3 p-2 rounded flex items-center gap-2 text-[10px]" style={{
          color: "#f59e0b",
          backgroundColor: "rgba(245,158,11,0.08)",
          border: "1px solid rgba(245,158,11,0.15)",
        }}>
          <AlertTriangle size={12} />
          超标: {data.violations.map(v => `${v.industry}(${v.count}>${v.limit})`).join(", ")}
        </div>
      )}

      {/* Pie chart + list */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
        {sorted.length > 0 && (
          <ReactECharts option={pieOpt} style={{ height: 220 }} />
        )}
        <div className="space-y-1" style={{ maxHeight: 220, overflowY: "auto" }}>
          {sorted.map(([name, count], i) => {
            const pct = data.holdings > 0 ? ((count / data.holdings) * 100) : 0;
            const over = count > data.industry_limit;
            return (
              <div key={i} className="flex items-center gap-2 p-1.5 rounded" style={{
                backgroundColor: over ? "rgba(239,68,68,0.05)" : "transparent",
              }}>
                <div className="text-[10px] flex-1 truncate" style={{ color: over ? "#ef4444" : "var(--text-secondary)" }}>
                  {name}
                </div>
                <div className="w-20 h-1.5 rounded-full" style={{ backgroundColor: "rgba(255,255,255,0.06)" }}>
                  <div className="h-full rounded-full transition-all" style={{
                    width: `${Math.min(pct * 3, 100)}%`,
                    backgroundColor: over ? "#ef4444" : pct > 15 ? "#f59e0b" : "#22c55e",
                  }} />
                </div>
                <div className="text-[9px] font-mono w-10 text-right" style={{ color: over ? "#ef4444" : "var(--text-muted)" }}>
                  {count}只
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
