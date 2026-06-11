"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, TrendingDown, Shield } from "lucide-react";
import ReactECharts from "echarts-for-react";

interface StressTestData {
  date: string;
  portfolio_value: number;
  holdings_count: number;
  summary?: {
    worst_historical: string;
    worst_historical_loss: number;
    worst_hypothetical: string;
    worst_hypothetical_loss: number;
    avg_historical_loss: number;
    avg_hypothetical_loss: number;
  };
  historical_scenarios?: Record<string, number>;
  hypothetical_scenarios?: Record<string, number>;
  var_analysis?: any;
  concentration_risk?: any;
}

export default function StressTestPanel() {
  const [data, setData] = useState<StressTestData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v25/stress-test")
      .then(r => r.json())
      .then(d => { if (d.date) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl p-6 animate-pulse" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
        <div className="h-4 w-28 rounded mb-4" style={{ background: "var(--border-color)" }} />
        <div className="h-48 rounded" style={{ background: "var(--border-color)", opacity: 0.3 }} />
      </div>
    );
  }

  if (!data) return null;

  const histEntries = Object.entries(data.historical_scenarios || {}).sort((a, b) => a[1] - b[1]);
  const hypoEntries = Object.entries(data.hypothetical_scenarios || {});
  const allScenarios = [...histEntries, ...hypoEntries];
  const maxLoss = Math.abs(Math.min(...allScenarios.map(e => e[1]), 0));

  const barOpt = {
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1e293b",
      textStyle: { color: "#e2e8f0", fontSize: 11 },
      formatter: (p: any) => `${p[0].name}<br/>损失: ${(-p[0].value).toFixed(1)}%`,
    },
    grid: { left: 10, right: 10, top: 5, bottom: 5 },
    xAxis: {
      type: "value",
      min: -maxLoss * 1.1,
      max: 0,
      axisLabel: { color: "#64748B", fontSize: 9, formatter: (v: number) => `${-v.toFixed(0)}%` },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
    },
    yAxis: {
      type: "category",
      data: allScenarios.map(e => e[0]).reverse(),
      axisLabel: { color: "#94a3b8", fontSize: 9 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: "bar",
      data: allScenarios.map(e => ({
        value: e[1],
        itemStyle: {
          color: e[1] < -15 ? "rgba(239,68,68,0.8)" : e[1] < -7 ? "rgba(245,158,11,0.7)" : "rgba(100,116,139,0.5)",
          borderRadius: [0, 4, 4, 0],
        },
      })),
      barWidth: 14,
    }],
  };

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle size={14} style={{ color: "#f59e0b" }} />
        <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
          压力测试
        </span>
        <span className="text-[10px] ml-auto" style={{ color: "var(--text-muted)" }}>
          {data.date}
        </span>
      </div>

      {/* Summary */}
      {data.summary && (
        <div className="grid grid-cols-4 gap-2 mb-4">
          <div className="p-2 rounded" style={{ backgroundColor: "rgba(239,68,68,0.05)" }}>
            <div className="text-[9px]" style={{ color: "var(--text-muted)" }}>最差历史</div>
            <div className="text-xs font-bold font-mono" style={{ color: "#ef4444" }}>
              {data.summary.worst_historical_loss?.toFixed(1)}%
            </div>
            <div className="text-[8px] truncate" style={{ color: "var(--text-muted)" }}>{data.summary.worst_historical}</div>
          </div>
          <div className="p-2 rounded" style={{ backgroundColor: "rgba(239,68,68,0.05)" }}>
            <div className="text-[9px]" style={{ color: "var(--text-muted)" }}>最差假设</div>
            <div className="text-xs font-bold font-mono" style={{ color: "#ef4444" }}>
              {data.summary.worst_hypothetical_loss?.toFixed(1)}%
            </div>
            <div className="text-[8px] truncate" style={{ color: "var(--text-muted)" }}>{data.summary.worst_hypothetical}</div>
          </div>
          <div className="p-2 rounded" style={{ backgroundColor: "rgba(245,158,11,0.05)" }}>
            <div className="text-[9px]" style={{ color: "var(--text-muted)" }}>平均历史</div>
            <div className="text-xs font-bold font-mono" style={{ color: "#f59e0b" }}>
              {data.summary.avg_historical_loss?.toFixed(1)}%
            </div>
          </div>
          <div className="p-2 rounded" style={{ backgroundColor: "rgba(59,130,246,0.05)" }}>
            <div className="text-[9px]" style={{ color: "var(--text-muted)" }}>平均假设</div>
            <div className="text-xs font-bold font-mono" style={{ color: "#3b82f6" }}>
              {data.summary.avg_hypothetical_loss?.toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* Bar chart */}
      <ReactECharts option={barOpt} style={{ height: Math.max(180, allScenarios.length * 22) }} />

      {/* VaR */}
      {data.var_analysis && (
        <div className="mt-3 pt-3 border-t flex gap-4 text-[10px]" style={{ borderColor: "var(--border-color)" }}>
          <span style={{ color: "var(--text-muted)" }}>
            VaR(95) <span className="font-mono" style={{ color: "#ef4444" }}>{data.var_analysis.var_95?.toFixed(1)}%</span>
          </span>
          <span style={{ color: "var(--text-muted)" }}>
            VaR(99) <span className="font-mono" style={{ color: "#ef4444" }}>{data.var_analysis.var_99?.toFixed(1)}%</span>
          </span>
          <span style={{ color: "var(--text-muted)" }}>
            CVaR <span className="font-mono" style={{ color: "#ef4444" }}>{data.var_analysis.cvar?.toFixed(1)}%</span>
          </span>
          <span style={{ color: "var(--text-muted)" }}>
            组合价值 <span className="font-mono" style={{ color: "var(--text-primary)" }}>{(data.portfolio_value / 10000).toFixed(0)}万</span>
          </span>
        </div>
      )}
    </div>
  );
}
