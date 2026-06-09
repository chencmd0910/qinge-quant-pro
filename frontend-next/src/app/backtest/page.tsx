"use client";

import { useEffect, useState, useMemo } from "react";
import {
  TrendingUp, TrendingDown, Target, Activity,
  BarChart3, DollarSign, Percent, Calendar, Loader2,
  Search, CheckCircle2, Circle, AlertTriangle, Layers,
} from "lucide-react";
import ReactECharts from "echarts-for-react";
import api from "@/lib/axios";
import RealBacktestRunner from "@/components/real-backtest/runner";

// ── Types ──

interface StrategySummary {
  id: string;
  name: string;
  type: string;
  version: string;
  annual_return: number;
  total_return: number;
  sharpe: number;
  max_dd: number;
  win_rate: number;
  trade_count: number;
  alpha?: number;
  score?: number;
  rank?: number;
  source: "real" | "registry";
  equity_curve: { date: string; value: number }[];
  drawdown_curve: { date: string; dd: number }[];
  trades: Trade[];
  annual_returns: Record<string, number>;
}

interface Trade {
  date: string;
  action?: string;
  side?: string;
  symbol: string;
  name: string;
  price: number;
  quantity: number;
}

// ── Helpers ──

const fmoney = (v: number) => {
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (Math.abs(v) >= 1e4) return `${(v / 1e4).toFixed(0)}万`;
  return v.toFixed(0);
};

const fpct = (v: number) => `${v >= 0 ? "+" : ""}${v?.toFixed(2) ?? 0}%`;

const typeLabel: Record<string, string> = {
  etf_rotation: "ETF轮动",
  multi_factor: "多因子",
  industry_rotation: "行业轮动",
  dividend: "红利",
};

const typeColor: Record<string, string> = {
  etf_rotation: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  multi_factor: "bg-violet-500/10 text-violet-400 border-violet-500/20",
  industry_rotation: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  dividend: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
};

// ── KPI Card ──

function KPI({ icon: Icon, label, value, color }: {
  icon: any; label: string; value: string; color: string;
}) {
  const clr: Record<string, string> = {
    emerald: "text-emerald-400",
    amber: "text-amber-400",
    red: "text-red-400",
    blue: "text-blue-400",
  };
  return (
    <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/30">
      <div className="flex items-center gap-2 mb-1.5">
        <Icon size={12} className={clr[color] || "text-slate-400"} />
        <span className="text-[10px] text-slate-500">{label}</span>
      </div>
      <div className={`text-lg font-bold font-mono ${clr[color] || "text-slate-300"}`}>{value}</div>
    </div>
  );
}

// ── Main Page ──

export default function BacktestPage() {
  const [strategies, setStrategies] = useState<StrategySummary[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [compareIds, setCompareIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/dashboard/strategies")
      .then(({ data }) => {
        const list: StrategySummary[] = data.strategies || [];
        setStrategies(list);
        if (list.length > 0) setSelected(list[0].id);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return strategies;
    const q = search.toLowerCase();
    return strategies.filter((s) =>
      s.name.toLowerCase().includes(q) ||
      s.type.toLowerCase().includes(q) ||
      (typeLabel[s.type] || "").includes(q)
    );
  }, [strategies, search]);

  const current = strategies.find((s) => s.id === selected);
  const compareList = strategies.filter((s) => compareIds.has(s.id));

  const toggleCompare = (id: string) => {
    setCompareIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // ── Equity chart ──

  const equityOption = useMemo(() => {
    if (!current) return {};
    const series: any[] = [
      {
        name: current.name,
        type: "line",
        data: current.equity_curve.map((p) => p.value),
        lineStyle: { color: "#22C55E", width: 2 },
        areaStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(34,197,94,0.15)" },
              { offset: 1, color: "rgba(34,197,94,0)" },
            ],
          },
        },
        showSymbol: false,
        smooth: true,
      },
    ];

    const compareColors = ["#3B82F6", "#A855F7", "#F59E0B", "#EC4899"];
    compareList.forEach((s, i) => {
      series.push({
        name: s.name,
        type: "line",
        data: s.equity_curve.map((p) => p.value),
        lineStyle: { color: compareColors[i % compareColors.length], width: 1.5, type: "dashed" },
        showSymbol: false,
        smooth: true,
      });
    });

    const dates = current.equity_curve.map((p) => p.date);

    return {
      backgroundColor: "transparent",
      grid: { top: 30, right: 20, bottom: 30, left: 70 },
      legend: {
        top: 6,
        textStyle: { color: "#94A3B8", fontSize: 10 },
        data: [current.name, ...compareList.map((s) => s.name)],
      },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: "#1F2937" } },
        axisLabel: { color: "#6B7280", fontSize: 10, formatter: (v: string) => v.slice(5) },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "#6B7280", fontSize: 10, formatter: (v: number) => fmoney(v) },
        splitLine: { lineStyle: { color: "#1F2937", type: "dashed" } },
      },
      series,
      tooltip: {
        trigger: "axis",
        backgroundColor: "#111827",
        borderColor: "#1F2937",
        textStyle: { color: "#E5E7EB", fontSize: 11 },
        formatter: (params: any) => {
          if (!Array.isArray(params)) params = [params];
          return `${params[0].axisValue}<br/>` +
            params.map((p: any) => 
              `${p.marker} ${p.seriesName}: ¥${p.value.toLocaleString()}`
            ).join("<br/>");
        },
      },
    };
  }, [current, compareList]);

  // ── Drawdown chart ──

  const ddOption = useMemo(() => {
    if (!current) return {};
    const hasDD = current.drawdown_curve.length > 0;
    if (!hasDD) return {};

    return {
      backgroundColor: "transparent",
      grid: { top: 10, right: 20, bottom: 30, left: 70 },
      xAxis: {
        type: "category",
        data: current.drawdown_curve.map((p) => p.date),
        axisLine: { lineStyle: { color: "#1F2937" } },
        axisLabel: { color: "#6B7280", fontSize: 10, formatter: (v: string) => v.slice(5) },
      },
      yAxis: {
        type: "value", max: 0,
        axisLabel: { color: "#EF4444", fontSize: 10, formatter: (v: number) => `${v.toFixed(0)}%` },
        splitLine: { lineStyle: { color: "#1F2937", type: "dashed" } },
      },
      series: [{
        type: "line",
        data: current.drawdown_curve.map((p) => p.dd),
        lineStyle: { color: "#EF4444", width: 1.5 },
        areaStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(239,68,68,0.15)" },
              { offset: 1, color: "rgba(239,68,68,0)" },
            ],
          },
        },
        showSymbol: false,
        smooth: true,
      }],
      tooltip: {
        trigger: "axis",
        backgroundColor: "#111827",
        borderColor: "#1F2937",
        textStyle: { color: "#E5E7EB", fontSize: 11 },
        formatter: (p: any) => `${p[0].axisValue}<br/>回撤: ${p[0].value}%`,
      },
    };
  }, [current]);

  // ── Annual returns chart ──

  const annualOption = useMemo(() => {
    if (!current || !current.annual_returns || Object.keys(current.annual_returns).length === 0) return {};
    const years = Object.keys(current.annual_returns).sort();
    const values = years.map((y) => current.annual_returns[y]);

    return {
      backgroundColor: "transparent",
      grid: { top: 10, right: 20, bottom: 30, left: 60 },
      xAxis: {
        type: "category",
        data: years,
        axisLine: { lineStyle: { color: "#1F2937" } },
        axisLabel: { color: "#6B7280", fontSize: 10 },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "#6B7280", fontSize: 10, formatter: (v: number) => `${v}%` },
        splitLine: { lineStyle: { color: "#1F2937", type: "dashed" } },
      },
      series: [{
        type: "bar",
        data: values.map((v, i) => ({
          value: v,
          itemStyle: { color: v >= 0 ? "#22C55E" : "#EF4444", borderRadius: [4, 4, 0, 0] },
        })),
        barWidth: "55%",
      }],
      tooltip: {
        trigger: "axis",
        backgroundColor: "#111827",
        borderColor: "#1F2937",
        textStyle: { color: "#E5E7EB", fontSize: 11 },
        formatter: (p: any) => `${p[0].axisValue}年: ${p[0].value}%`,
      },
    };
  }, [current]);

  // ── Loading / Empty ──

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={24} className="animate-spin text-emerald-400" />
      </div>
    );
  }

  if (strategies.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-slate-500 text-sm">暂无回测数据，请先运行回测</span>
      </div>
    );
  }

  // ── Render ──

  const dataBadge = current?.source === "real"
    ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
    : "text-amber-400 bg-amber-500/10 border-amber-500/20";

  const dataLabel = current?.source === "real" ? "真实回测" : "注册表数据";

  return (
    <div className="h-full overflow-auto">
      <div className="h-full flex gap-0">
        {/* ── LEFT: Strategy List ── */}
        <div className="w-72 flex-shrink-0 border-r border-slate-800 bg-slate-900/40 flex flex-col">
          <div className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                <BarChart3 size={14} />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-white">回测中心</h1>
                <p className="text-[10px] text-slate-500">{strategies.length} 个策略</p>
              </div>
            </div>
            <div className="mb-3">
              <RealBacktestRunner />
            </div>

            <div className="relative mb-3">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-600" />
              <input
                type="text"
                placeholder="搜索策略..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full h-8 pl-8 pr-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
              />
            </div>

            {compareIds.size > 0 && (
              <div className="mb-3">
                <button
                  onClick={() => setCompareIds(new Set())}
                  className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <Layers size={10} /> 清除对比 ({compareIds.size})
                </button>
              </div>
            )}
          </div>

          <div className="flex-1 overflow-auto px-3 pb-3 space-y-1">
            {filtered.map((s) => {
              const isSelected = selected === s.id;
              const isCompared = compareIds.has(s.id);
              return (
                <div
                  key={s.id}
                  onClick={() => setSelected(s.id)}
                  className={`group rounded-lg p-3 cursor-pointer transition-all border ${
                    isSelected
                      ? "bg-blue-500/10 border-blue-500/30"
                      : "bg-slate-800/40 border-transparent hover:border-slate-700/50"
                  }`}
                >
                  <div className="flex items-start justify-between mb-1.5">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className={`text-xs font-semibold truncate ${isSelected ? "text-blue-400" : "text-white"}`}>
                          {s.name}
                        </span>
                        <span className={`text-[9px] px-1 py-0.5 rounded border ${typeColor[s.type] || "text-slate-400 bg-slate-500/10 border-slate-500/20"}`}>
                          {typeLabel[s.type] || s.type}
                        </span>
                      </div>
                      <div className="text-[9px] text-slate-600 mt-0.5">{s.version}</div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleCompare(s.id);
                      }}
                      className="p-0.5 rounded hover:bg-slate-700/50 transition-colors ml-1 flex-shrink-0"
                      title="加入对比"
                    >
                      {isCompared
                        ? <CheckCircle2 size={14} className="text-blue-400" />
                        : <Circle size={14} className="text-slate-600 group-hover:text-slate-400" />
                      }
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-1.5 text-[10px]">
                    <div>
                      <span className="text-slate-600">夏普</span>
                      <div className={`font-mono font-bold ${s.sharpe >= 1 ? "text-emerald-400" : s.sharpe >= 0.5 ? "text-amber-400" : "text-red-400"}`}>
                        {s.sharpe.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-600">年化</span>
                      <div className={`font-mono font-bold ${s.annual_return >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {fpct(s.annual_return)}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-600">回撤</span>
                      <div className={`font-mono font-bold ${Math.abs(s.max_dd) < 15 ? "text-emerald-400" : Math.abs(s.max_dd) < 25 ? "text-amber-400" : "text-red-400"}`}>
                        {s.max_dd}%
                      </div>
                    </div>
                  </div>

                  {s.source === "real" && (
                    <div className="mt-1.5 flex items-center gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span className="text-[9px] text-emerald-400">真实回测数据</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* ── RIGHT: Detail ── */}
        <div className="flex-1 overflow-auto p-6 space-y-4 min-w-0">
          {current ? (
            <>
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-lg font-semibold text-white">{current.name}</h1>
                    <span className={`text-[9px] px-2 py-0.5 rounded border ${typeColor[current.type] || "text-slate-400 border-slate-500/20 bg-slate-500/10"}`}>
                      {typeLabel[current.type] || current.type}
                    </span>
                    <span className={`text-[9px] px-2 py-0.5 rounded border ${dataBadge}`}>
                      {dataLabel}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    回测区间: 2018-01 → 2026-06 · {current.trade_count} 笔交易
                    {current.alpha !== undefined && ` · Alpha: ${fpct(current.alpha)}`}
                  </p>
                </div>
                {compareList.length > 0 && (
                  <div className="text-[10px] text-slate-500 flex items-center gap-1">
                    <Layers size={12} /> 已叠加 {compareList.map((s) => s.name).join(", ")} 权益曲线
                  </div>
                )}
              </div>

              {/* KPI Row 1 */}
              <div className="grid grid-cols-4 gap-3">
                <KPI icon={DollarSign} label="累计收益" value={fpct(current.total_return)}
                  color={current.total_return >= 0 ? "emerald" : "red"} />
                <KPI icon={TrendingUp} label="年化收益" value={fpct(current.annual_return)}
                  color={current.annual_return >= 0 ? "emerald" : "red"} />
                <KPI icon={Target} label="夏普比率" value={current.sharpe.toFixed(2)}
                  color={current.sharpe >= 1 ? "emerald" : current.sharpe >= 0.5 ? "amber" : "red"} />
                <KPI icon={TrendingDown} label="最大回撤" value={`${current.max_dd}%`}
                  color={Math.abs(current.max_dd) < 15 ? "emerald" : Math.abs(current.max_dd) < 25 ? "amber" : "red"} />
              </div>

              {/* KPI Row 2 */}
              <div className="grid grid-cols-4 gap-3">
                <KPI icon={Activity} label="交易笔数" value={String(current.trade_count)} color="blue" />
                <KPI icon={Percent} label="胜率" value={`${current.win_rate}%`}
                  color={current.win_rate >= 55 ? "emerald" : "amber"} />
                <KPI icon={Calendar} label="回测区间" value="2018-2026" color="blue" />
                <KPI icon={Target} label="策略版本" value={current.version} color="blue" />
              </div>

              {/* Equity Curve */}
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/30">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold text-white">权益曲线</h3>
                  {current.source !== "real" && (
                    <span className="text-[9px] text-amber-400 flex items-center gap-1">
                      <AlertTriangle size={10} /> 模拟曲线（基于年化收益+回撤生成）
                    </span>
                  )}
                </div>
                <ReactECharts option={equityOption} style={{ height: 320 }} />
              </div>

              {/* Drawdown Curve */}
              {current.drawdown_curve.length > 0 && (
                <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/30">
                  <h3 className="text-xs font-semibold mb-3 text-white">回撤曲线</h3>
                  <ReactECharts option={ddOption} style={{ height: 200 }} />
                </div>
              )}

              {/* Annual Returns */}
              {current.annual_returns && Object.keys(current.annual_returns).length > 0 && (
                <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/30">
                  <h3 className="text-xs font-semibold mb-3 text-white">年度收益</h3>
                  <ReactECharts option={annualOption} style={{ height: 200 }} />
                  <div className="flex gap-2 mt-3 flex-wrap">
                    {Object.entries(current.annual_returns).sort().map(([year, v]) => (
                      <div key={year} className={`px-2.5 py-1 rounded text-[10px] font-mono ${
                        v >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                      }`}>
                        {year}: {fpct(v)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Trades */}
              {current.trades.length > 0 && (
                <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/30">
                  <h3 className="text-xs font-semibold mb-3 text-white">
                    交易明细 ({current.trades.length} 笔)
                  </h3>
                  <div className="overflow-x-auto max-h-80 overflow-y-auto">
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 bg-slate-800/90">
                        <tr className="text-slate-500 border-b border-slate-700">
                          <th className="text-left py-2 px-2">日期</th>
                          <th className="text-left py-2 px-2">操作</th>
                          <th className="text-left py-2 px-2">代码</th>
                          <th className="text-left py-2 px-2">名称</th>
                          <th className="text-right py-2 px-2">价格</th>
                          <th className="text-right py-2 px-2">数量</th>
                        </tr>
                      </thead>
                      <tbody>
                        {current.trades.slice(-50).reverse().map((t, i) => {
                          const act = t.action || t.side || "";
                          const isBuy = act === "买入" || act === "BUY" || act === "buy";
                          return (
                            <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-700/20">
                              <td className="py-1.5 px-2 text-slate-400">{t.date}</td>
                              <td className="py-1.5 px-2">
                                <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                  isBuy ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                                }`}>
                                  {act}
                                </span>
                              </td>
                              <td className="py-1.5 px-2 font-mono text-slate-400">{t.symbol}</td>
                              <td className="py-1.5 px-2">{t.name || "-"}</td>
                              <td className="py-1.5 px-2 text-right font-mono">¥{t.price?.toFixed(2)}</td>
                              <td className="py-1.5 px-2 text-right font-mono text-slate-400">{t.quantity}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <span className="text-slate-500">请从左侧选择一个策略</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
