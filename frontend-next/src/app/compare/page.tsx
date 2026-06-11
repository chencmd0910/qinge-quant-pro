"use client";

import { useEffect, useState, useCallback } from "react";
import { BarChart3, TrendingUp, Trophy, FlaskConical, Activity } from "lucide-react";
import ReactECharts from "echarts-for-react";

interface StrategySummary {
  id?: string;
  strategy_id?: string;
  strategy_name: string;
  status?: string;
  total_return?: number;
  sharpe?: number;
  max_drawdown?: number;
  win_rate?: number;
  annual_return?: number;
  trade_count?: number;
  positions?: number;
}

interface GenealogySummary {
  total_strategies: number;
  total_generations: number;
  best_sharpe?: number;
  best_return?: number;
  active_count?: number;
  strategies?: StrategySummary[];
}

export default function ComparePage() {
  const [genealogy, setGenealogy] = useState<GenealogySummary | null>(null);
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    try {
      const [genRes, stratRes] = await Promise.all([
        fetch("/api/ai/genealogy/summary").then(r => r.json()).catch(() => null),
        fetch("/api/ai/strategies").then(r => r.json()).catch(() => null),
      ]);
      
      if (genRes && !genRes.error) {
        setGenealogy(genRes);
      }
      
      let strats: StrategySummary[] = [];
      if (Array.isArray(stratRes)) {
        strats = stratRes;
      } else if (stratRes?.strategies) {
        strats = stratRes.strategies;
      } else if (genRes?.strategies) {
        strats = genRes.strategies;
      }
      
      setStrategies(strats);
      // Auto-select top 5
      const top5 = new Set(strats.slice(0, 5).map(s => s.strategy_name || s.id || ""));
      setSelected(top5);
    } catch {}
    setLoading(false);
  }, []);
  
  useEffect(() => { load(); }, [load]);

  const toggleSelect = (name: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const activeStrats = strategies.filter(s => s.status === "ACTIVE" || s.status === "active");
  const allStrats = strategies.length > 0 ? strategies : activeStrats;

  // Radar chart data
  const selectedStrats = allStrats.filter(s => selected.has(s.strategy_name || s.id || ""));
  
  const radarOpt = selectedStrats.length > 0 ? {
    tooltip: { backgroundColor: "#1e293b", textStyle: { color: "#e2e8f0", fontSize: 12 } },
    legend: {
      data: selectedStrats.map(s => s.strategy_name || s.id),
      bottom: 0,
      textStyle: { color: "#94a3b8", fontSize: 10 },
    },
    radar: {
      indicator: [
        { name: "Sharpe", max: 3 },
        { name: "Return%", max: 100 },
        { name: "WinRate%", max: 100 },
        { name: "Drawdown", max: 100 },
      ],
      shape: "circle",
      center: ["50%", "45%"],
      radius: "65%",
      axisName: { color: "#94a3b8", fontSize: 10 },
    },
    series: [{
      type: "radar",
      data: selectedStrats.map((s, i) => ({
        name: s.strategy_name || s.id,
        value: [
          Math.abs(s.sharpe || 0) * 2,
          Math.abs(s.total_return || 0),
          s.win_rate || 50,
          Math.abs(s.max_drawdown || 0) * 2,
        ],
        lineStyle: { color: ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"][i % 5] },
        areaStyle: { color: ["rgba(34,197,94,0.1)", "rgba(59,130,246,0.1)", "rgba(245,158,11,0.1)", "rgba(239,68,68,0.1)", "rgba(139,92,246,0.1)"][i % 5] },
      })),
    }],
  } : null;

  const barOpt = selectedStrats.length > 0 ? {
    tooltip: { backgroundColor: "#1e293b", textStyle: { color: "#e2e8f0", fontSize: 12 } },
    grid: { left: 100, right: 20, top: 10, bottom: 10 },
    xAxis: {
      type: "value",
      axisLabel: { color: "#94a3b8", fontSize: 10 },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
    },
    yAxis: {
      type: "category",
      data: selectedStrats.map(s => (s.strategy_name || s.id || "").slice(0, 12)),
      axisLabel: { color: "#e2e8f0", fontSize: 10 },
    },
    series: [
      {
        name: "Return %",
        type: "bar",
        data: selectedStrats.map((s, i) => ({
          value: s.total_return || 0,
          itemStyle: {
            color: (s.total_return || 0) >= 0 ? "rgba(34,197,94,0.7)" : "rgba(239,68,68,0.7)",
            borderRadius: [0, 4, 4, 0],
          },
        })),
        barWidth: "50%",
      },
    ],
  } : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
          <Trophy size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            策略对比
          </h1>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            多策略收益对比 · 雷达图 · 基因库概览
          </p>
        </div>
        {genealogy && (
          <div className="ml-auto flex items-center gap-4 text-xs">
            <span style={{ color: "var(--text-muted)" }}>
              <strong style={{ color: "var(--accent)" }}>{genealogy.total_strategies}</strong> 策略
            </span>
            <span style={{ color: "var(--text-muted)" }}>
              <strong style={{ color: "var(--text-primary)" }}>{genealogy.total_generations}</strong> 代进化
            </span>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20" style={{ color: "var(--text-muted)" }}>
          <Activity size={20} className="animate-pulse" />
        </div>
      ) : (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-5 gap-3">
            <KpiCard label="总策略数" value={genealogy?.total_strategies || allStrats.length} color="#22c55e" />
            <KpiCard label="进化代数" value={genealogy?.total_generations || 0} color="#3b82f6" />
            <KpiCard label="活跃策略" value={activeStrats.length} color="#f59e0b" />
            <KpiCard label="历史最佳Sharpe" value={(genealogy?.best_sharpe || 0).toFixed(2)} color="#8b5cf6" suffix="" />
            <KpiCard label="历史最佳收益" value={(genealogy?.best_return || 0).toFixed(1)} color="#ef4444" suffix="%" />
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {radarOpt && (
              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="flex items-center gap-2 mb-2">
                  <Activity size={14} style={{ color: "var(--accent)" }} />
                  <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>能力雷达图</span>
                </div>
                <ReactECharts option={radarOpt} style={{ height: 300 }} />
              </div>
            )}
            {barOpt && (
              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 size={14} style={{ color: "#22c55e" }} />
                  <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>收益对比</span>
                </div>
                <ReactECharts option={barOpt} style={{ height: 300 }} />
              </div>
            )}
          </div>

          {/* Strategy list */}
          {allStrats.length > 0 && (
            <div className="rounded-xl overflow-hidden" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
              <div className="p-4 pb-2 flex items-center gap-2">
                <FlaskConical size={14} style={{ color: "var(--accent)" }} />
                <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
                  策略列表（点击选中对比）
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                      <th className="p-3 text-left" style={{ color: "var(--text-muted)" }}>名称</th>
                      <th className="p-3 text-right" style={{ color: "var(--text-muted)" }}>状态</th>
                      <th className="p-3 text-right" style={{ color: "var(--text-muted)" }}>收益</th>
                      <th className="p-3 text-right" style={{ color: "var(--text-muted)" }}>Sharpe</th>
                      <th className="p-3 text-right" style={{ color: "var(--text-muted)" }}>回撤</th>
                      <th className="p-3 text-right" style={{ color: "var(--text-muted)" }}>胜率</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allStrats.map((s, i) => {
                      const name = s.strategy_name || s.id || `Strategy ${i}`;
                      const isSelected = selected.has(name);
                      return (
                        <tr
                          key={name}
                          onClick={() => toggleSelect(name)}
                          className="cursor-pointer transition-colors hover:bg-white/[0.02]"
                          style={{
                            borderBottom: "1px solid var(--border-color)",
                            backgroundColor: isSelected ? "rgba(34,197,94,0.05)" : "transparent",
                          }}
                        >
                          <td className="p-3 flex items-center gap-2">
                            <div
                              className="w-2 h-2 rounded-full flex-shrink-0"
                              style={{
                                backgroundColor: isSelected ? "#22c55e" : "var(--border-color)",
                              }}
                            />
                            <span style={{ color: "var(--text-primary)" }}>{name}</span>
                          </td>
                          <td className="p-3 text-right">
                            <span className="px-1.5 py-0.5 rounded text-[10px]" style={{
                              backgroundColor: (s.status || "").toUpperCase() === "ACTIVE" ? "rgba(34,197,94,0.15)" : "rgba(100,116,139,0.15)",
                              color: (s.status || "").toUpperCase() === "ACTIVE" ? "#22c55e" : "#94a3b8",
                            }}>
                              {s.status || "UNKNOWN"}
                            </span>
                          </td>
                          <td className="p-3 text-right font-mono" style={{ color: (s.total_return || 0) >= 0 ? "#22c55e" : "#ef4444" }}>
                            {(s.total_return || 0) >= 0 ? "+" : ""}{(s.total_return || 0).toFixed(1)}%
                          </td>
                          <td className="p-3 text-right font-mono" style={{ color: "var(--text-secondary)" }}>
                            {(s.sharpe || 0).toFixed(2)}
                          </td>
                          <td className="p-3 text-right font-mono" style={{ color: "#ef4444" }}>
                            {(s.max_drawdown || 0).toFixed(1)}%
                          </td>
                          <td className="p-3 text-right font-mono" style={{ color: "var(--text-secondary)" }}>
                            {(s.win_rate || 0).toFixed(0)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function KpiCard({ label, value, color, suffix }: { label: string; value: string | number; color: string; suffix?: string }) {
  return (
    <div className="rounded-xl p-3 text-center" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>{label}</div>
      <div className="text-lg font-bold font-mono" style={{ color }}>{value}{suffix || ""}</div>
    </div>
  );
}
