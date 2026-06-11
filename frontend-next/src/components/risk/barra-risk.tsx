"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { BarChart3 } from "lucide-react";

export default function BarraRisk() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v25/barra-risk")
      .then(r => r.json())
      .then(d => { if (!d.error) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl p-6 animate-pulse" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
        <div className="h-4 w-24 rounded mb-4" style={{ background: "var(--border-color)" }} />
        <div className="h-48 rounded" style={{ background: "var(--border-color)", opacity: 0.3 }} />
      </div>
    );
  }

  if (!data) return null;

  const summary = data.risk_budget_summary || {};
  const exposures = data.factor_exposures?.weighted_portfolio || {};
  const decomp = data.risk_decomposition || {};

  // Top risk factors from factor_contribution
  const topFactors = data.factor_contribution?.by_factor
    ? Object.entries(data.factor_contribution.by_factor)
        .sort((a, b) => (b[1] as any).risk_contribution_pct - (a[1] as any).risk_contribution_pct)
        .slice(0, 5)
        .map(([name, info]: [string, any]) => `${name} ${info.risk_contribution_pct.toFixed(1)}%`)
    : [];

  // Bar chart option
  const expEntries = Object.entries(exposures).map(([k, v]) => ({
    name: k,
    value: v as number,
  }));

  const barOpt = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "#1e293b",
      textStyle: { color: "#e2e8f0", fontSize: 12 },
      formatter: (p: any) => {
        const v = p[0].value;
        return `${p[0].name}<br/>暴露: ${v > 0 ? "+" : ""}${v.toFixed(3)}`;
      },
    },
    grid: { left: 15, right: 15, top: 10, bottom: 5 },
    xAxis: {
      type: "value",
      min: -0.8,
      max: 0.8,
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
      axisLabel: { color: "#64748B", fontSize: 10 },
    },
    yAxis: {
      type: "category",
      data: expEntries.map(e => e.name),
      axisLabel: { color: "#94a3b8", fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: "bar",
      data: expEntries.map(e => ({
        value: e.value,
        itemStyle: {
          color: e.value > 0 ? "rgba(34,197,94,0.7)" : "rgba(239,68,68,0.7)",
          borderRadius: e.value > 0 ? [0, 4, 4, 0] : [4, 0, 0, 4],
        },
      })),
      barWidth: 14,
    }],
  };

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 size={14} style={{ color: "var(--accent-blue)" }} />
        <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
          Barra 风险归因 (CNE6)
        </span>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="p-3 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.03)" }}>
          <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>风险等级</div>
          <div className="text-sm font-bold mt-0.5" style={{
            color: summary.risk_color === "green" ? "#22c55e" : summary.risk_color === "yellow" ? "#eab308" : "#ef4444",
          }}>
            {summary.risk_level || "--"}
          </div>
        </div>
        <div className="p-3 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.03)" }}>
          <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>年化波动</div>
          <div className="text-sm font-bold font-mono mt-0.5" style={{ color: "#eab308" }}>
            {summary.annual_volatility != null ? `${(summary.annual_volatility * 100).toFixed(1)}%` : "--"}
          </div>
        </div>
        <div className="p-3 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.03)" }}>
          <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>有效分散</div>
          <div className="text-sm font-bold font-mono mt-0.5" style={{ color: "var(--accent-blue)" }}>
            {decomp.effective_rank?.toFixed(1) || "--"}
          </div>
        </div>
      </div>

      {/* Top risk factors */}
      {topFactors.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {topFactors.map((f, i) => (
            <span key={i} className="text-[10px] px-2 py-0.5 rounded-full" style={{
              color: "#eab308",
              backgroundColor: "rgba(234,179,8,0.1)",
              border: "1px solid rgba(234,179,8,0.2)",
            }}>
              {f}
            </span>
          ))}
        </div>
      )}

      {/* Bar chart */}
      <ReactECharts option={barOpt} style={{ height: Math.max(160, expEntries.length * 28) }} theme="dark" />
    </div>
  );
}
