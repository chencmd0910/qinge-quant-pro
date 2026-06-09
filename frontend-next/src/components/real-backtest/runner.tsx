"use client";

import { useState, useMemo, useCallback } from "react";
import {
  Play, Loader2, TrendingUp, TrendingDown, Target,
  DollarSign, Percent, Calendar, Activity, Zap,
  AlertTriangle, Settings2, BarChart3, X, CheckCircle2,
} from "lucide-react";
import ReactECharts from "echarts-for-react";
import { runRealBacktest, RealBacktestResult } from "@/services/backtest";

// ── Presets ──

const PRESETS = [
  { label: "白马等权×10", start: "2025-06-01", end: "2026-06-09", top_n: 10, cash: 1_000_000 },
  { label: "300动量×20(1Y)", start: "2025-06-01", end: "2026-06-09", top_n: 20, cash: 1_000_000 },
  { label: "300动量×20(2Y)", start: "2024-06-01", end: "2026-06-09", top_n: 20, cash: 1_000_000 },
  { label: "300动量×30(1Y)", start: "2025-06-01", end: "2026-06-09", top_n: 30, cash: 1_000_000 },
];

// ── Helpers ──

const fmoney = (v: number) => {
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (Math.abs(v) >= 1e4) return `${(v / 1e4).toFixed(0)}万`;
  return v.toFixed(0);
};

const fpct = (v: number) => `${v >= 0 ? "+" : ""}${v?.toFixed(2) ?? 0}%`;

// ── KPI ──

function KPI({ icon: Icon, label, value, color }: {
  icon: any; label: string; value: string; color: string;
}) {
  const clr: Record<string, string> = {
    emerald: "text-emerald-400",
    amber: "text-amber-400",
    red: "text-red-400",
    blue: "text-blue-400",
    violet: "text-violet-400",
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

// ── Main Component ──

export default function RealBacktestRunner() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<RealBacktestResult | null>(null);

  // Form state
  const [start, setStart] = useState("2025-06-01");
  const [end, setEnd] = useState("2026-06-09");
  const [topN, setTopN] = useState(20);
  const [cash, setCash] = useState(1_000_000);
  const [rebalance, setRebalance] = useState("monthly");
  const [stopLoss, setStopLoss] = useState(-8);
  const [commission, setCommission] = useState(0.03);
  const [slippage, setSlippage] = useState(0.02);

  const applyPreset = useCallback((p: typeof PRESETS[0]) => {
    setStart(p.start);
    setEnd(p.end);
    setTopN(p.top_n);
    setCash(p.cash);
  }, []);

  const run = useCallback(async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await runRealBacktest({
        start, end, cash, top_n: topN, rebalance,
        stop_loss: stopLoss / 100,
        commission: commission / 100,
        slippage: slippage / 100,
        ranking_factor: "v25_multi",
        strategy_id: `frontend-${Date.now()}`,
      });
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "回测失败");
    } finally {
      setLoading(false);
    }
  }, [start, end, topN, cash, rebalance, stopLoss, commission, slippage]);

  // ── Equity Chart ──
  const equityOption = useMemo(() => {
    if (!result?.equity_curve) return {};
    const data = result.equity_curve;
    const dates = data.map((p) => p.date);
    const values = data.map((p) => p.value);
    const initCash = cash || 1_000_000;
    const benchmark = dates.map((_, i) => {
      // Simple benchmark: 3.5% annual return
      const years = i / 252;
      return Math.round(initCash * Math.pow(1.035, years));
    });

    return {
      backgroundColor: "transparent",
      grid: { top: 30, right: 20, bottom: 30, left: 70 },
      legend: { top: 6, textStyle: { color: "#94A3B8", fontSize: 10 },
        data: ["策略权益", "现金基准"] },
      xAxis: {
        type: "category", data: dates,
        axisLine: { lineStyle: { color: "#1F2937" } },
        axisLabel: { color: "#6B7280", fontSize: 10, formatter: (v: string) => v?.slice(5) || v },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "#6B7280", fontSize: 10, formatter: (v: number) => fmoney(v) },
        splitLine: { lineStyle: { color: "#1F2937", type: "dashed" } },
      },
      series: [
        {
          name: "策略权益", type: "line", data: values,
          lineStyle: { color: "#22C55E", width: 2 },
          areaStyle: {
            color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [{ offset: 0, color: "rgba(34,197,94,0.15)" }, { offset: 1, color: "rgba(34,197,94,0)" }] },
          },
          showSymbol: false, smooth: true,
        },
        {
          name: "现金基准", type: "line", data: benchmark,
          lineStyle: { color: "#64748B", width: 1, type: "dashed" },
          showSymbol: false, smooth: true,
        },
      ],
      tooltip: {
        trigger: "axis",
        backgroundColor: "#111827", borderColor: "#1F2937",
        textStyle: { color: "#E5E7EB", fontSize: 11 },
        formatter: (params: any) => {
          if (!Array.isArray(params)) params = [params];
          return `${params[0].axisValue}<br/>` +
            params.map((p: any) => `${p.marker} ${p.seriesName}: ¥${(p.value || 0).toLocaleString()}`).join("<br/>");
        },
      },
    };
  }, [result, cash]);

  // ── Drawdown from equity curve ──
  const ddData = useMemo(() => {
    if (!result?.equity_curve) return [];
    let peak = 0;
    return result.equity_curve.map((p) => {
      peak = Math.max(peak, p.value);
      return { date: p.date, dd: Math.round((p.value - peak) / peak * 10000) / 100 };
    });
  }, [result]);

  const ddOption = useMemo(() => {
    if (ddData.length === 0) return {};
    return {
      backgroundColor: "transparent",
      grid: { top: 10, right: 20, bottom: 30, left: 70 },
      xAxis: {
        type: "category", data: ddData.map((p) => p.date),
        axisLine: { lineStyle: { color: "#1F2937" } },
        axisLabel: { color: "#6B7280", fontSize: 10, formatter: (v: string) => v?.slice(5) || v },
      },
      yAxis: {
        type: "value", max: 0,
        axisLabel: { color: "#EF4444", fontSize: 10, formatter: (v: number) => `${v.toFixed(0)}%` },
        splitLine: { lineStyle: { color: "#1F2937", type: "dashed" } },
      },
      series: [{
        type: "line", data: ddData.map((p) => p.dd),
        lineStyle: { color: "#EF4444", width: 1.5 },
        areaStyle: {
          color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: "rgba(239,68,68,0.15)" }, { offset: 1, color: "rgba(239,68,68,0)" }] },
        },
        showSymbol: false, smooth: true,
      }],
      tooltip: {
        trigger: "axis",
        backgroundColor: "#111827", borderColor: "#1F2937",
        textStyle: { color: "#E5E7EB", fontSize: 11 },
        formatter: (p: any) => `${p[0].axisValue}<br/>回撤: ${p[0].value}%`,
      },
    };
  }, [ddData]);

  return (
    <>
      {/* ── Trigger Button ── */}
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-sm font-semibold hover:from-emerald-400 hover:to-teal-400 transition-all shadow-lg shadow-emerald-500/20"
      >
        <Zap size={16} />
        运行真实回测
      </button>

      {/* ── Modal ── */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[5vh] bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 rounded-2xl border border-slate-700/50 shadow-2xl w-[960px] max-h-[90vh] overflow-auto">
            {/* Header */}
            <div className="sticky top-0 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800 p-5 flex items-center justify-between z-10">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                  <BarChart3 size={16} />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-white">真实K线回测</h2>
                  <p className="text-[10px] text-slate-500">基于本地Parquet K线数据 · v25多因子 · 等权重再平衡</p>
                </div>
              </div>
              <button onClick={() => setOpen(false)}
                className="p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-500 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div className="p-6 space-y-5">
              {/* ── Presets ── */}
              <div>
                <div className="text-[10px] text-slate-500 mb-2 flex items-center gap-1.5">
                  <Settings2 size={11} /> 快速预设
                </div>
                <div className="flex gap-2 flex-wrap">
                  {PRESETS.map((p) => (
                    <button
                      key={p.label}
                      onClick={() => applyPreset(p)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300 hover:border-emerald-500/40 hover:text-emerald-400 transition-all"
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* ── Form ── */}
              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">起始日期</label>
                  <input type="text" value={start} onChange={(e) => setStart(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-emerald-500/50" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">结束日期</label>
                  <input type="text" value={end} onChange={(e) => setEnd(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-emerald-500/50" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">持仓数量</label>
                  <input type="number" value={topN} onChange={(e) => setTopN(+e.target.value)}
                    className="w-full h-9 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-emerald-500/50" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">初始资金(万)</label>
                  <input type="number" value={cash / 10000} onChange={(e) => setCash(+e.target.value * 10000)}
                    className="w-full h-9 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-emerald-500/50" />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">调仓频率</label>
                  <select value={rebalance} onChange={(e) => setRebalance(e.target.value)}
                    className="w-full h-9 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-emerald-500/50">
                    <option value="monthly">月度</option>
                    <option value="biweekly">双周</option>
                    <option value="weekly">周度</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">止损线(%)</label>
                  <input type="number" value={stopLoss} onChange={(e) => setStopLoss(+e.target.value)}
                    className="w-full h-9 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-emerald-500/50" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">手续费(%)</label>
                  <input type="number" value={commission} onChange={(e) => setCommission(+e.target.value)} step="0.01"
                    className="w-full h-9 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-emerald-500/50" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">滑点(%)</label>
                  <input type="number" value={slippage} onChange={(e) => setSlippage(+e.target.value)} step="0.01"
                    className="w-full h-9 px-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white font-mono focus:outline-none focus:border-emerald-500/50" />
                </div>
              </div>

              {/* ── Run Button ── */}
              <div className="flex items-center gap-3">
                <button
                  onClick={run}
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-sm font-semibold hover:from-emerald-400 hover:to-teal-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                  {loading ? "回测运行中..." : "开始回测"}
                </button>
                {loading && (
                  <span className="text-[10px] text-slate-500 flex items-center gap-1">
                    <Loader2 size={10} className="animate-spin" /> 加载4965只股票K线数据中...
                  </span>
                )}
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-center gap-2">
                  <AlertTriangle size={14} /> {error}
                </div>
              )}

              {/* ── Results ── */}
              {result && (
                <div className="space-y-4 pt-2 border-t border-slate-800">
                  {/* Result header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 size={14} className="text-emerald-400" />
                      <span className="text-sm font-semibold text-white">回测完成</span>
                      <span className="text-[10px] text-slate-500">
                        {result.start_date} → {result.end_date} · {result.trades.length}笔交易 · 数据源: {result.data_source}
                      </span>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-6 gap-2">
                    <KPI icon={DollarSign} label="累计收益" value={fpct(result.metrics.total_return)}
                      color={result.metrics.total_return >= 0 ? "emerald" : "red"} />
                    <KPI icon={TrendingUp} label="年化收益" value={fpct(result.metrics.annual_return)}
                      color={result.metrics.annual_return >= 0 ? "emerald" : "red"} />
                    <KPI icon={Target} label="夏普比率" value={result.metrics.sharpe_ratio.toFixed(2)}
                      color={result.metrics.sharpe_ratio >= 1 ? "emerald" : result.metrics.sharpe_ratio >= 0.5 ? "amber" : "red"} />
                    <KPI icon={TrendingDown} label="最大回撤" value={`${result.metrics.max_drawdown}%`}
                      color={Math.abs(result.metrics.max_drawdown) < 15 ? "emerald" : Math.abs(result.metrics.max_drawdown) < 25 ? "amber" : "red"} />
                    <KPI icon={Percent} label="胜率" value={`${result.metrics.win_rate}%`}
                      color={result.metrics.win_rate >= 55 ? "emerald" : "amber"} />
                    <KPI icon={Activity} label="交易笔数" value={String(result.trades.length)} color="violet" />
                  </div>

                  {/* Equity Curve */}
                  <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/30">
                    <h3 className="text-xs font-semibold text-white mb-3">权益曲线</h3>
                    <ReactECharts option={equityOption} style={{ height: 260 }} />
                  </div>

                  {/* Drawdown */}
                  {ddData.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/30">
                      <h3 className="text-xs font-semibold text-white mb-3">回撤曲线</h3>
                      <ReactECharts option={ddOption} style={{ height: 160 }} />
                    </div>
                  )}

                  {/* Trades */}
                  <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/30">
                    <h3 className="text-xs font-semibold text-white mb-3">交易明细 ({result.trades.length} 笔)</h3>
                    <div className="overflow-x-auto max-h-64 overflow-y-auto">
                      <table className="w-full text-xs">
                        <thead className="sticky top-0 bg-slate-800/95">
                          <tr className="text-slate-500 border-b border-slate-700">
                            <th className="text-left py-2 px-2">日期</th>
                            <th className="text-left py-2 px-2">方向</th>
                            <th className="text-left py-2 px-2">代码</th>
                            <th className="text-right py-2 px-2">价格</th>
                            <th className="text-right py-2 px-2">数量</th>
                            <th className="text-right py-2 px-2">金额</th>
                            <th className="text-left py-2 px-2">原因</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.trades.slice(-100).reverse().map((t, i) => {
                            const isBuy = t.side === "BUY";
                            return (
                              <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-700/20">
                                <td className="py-1.5 px-2 text-slate-400 font-mono">{t.date}</td>
                                <td className="py-1.5 px-2">
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${isBuy ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                                    {isBuy ? "买入" : "卖出"}
                                  </span>
                                </td>
                                <td className="py-1.5 px-2 font-mono text-slate-300">{t.symbol}</td>
                                <td className="py-1.5 px-2 text-right font-mono text-slate-400">¥{t.price?.toFixed(2)}</td>
                                <td className="py-1.5 px-2 text-right font-mono text-slate-400">{t.quantity.toLocaleString()}</td>
                                <td className="py-1.5 px-2 text-right font-mono text-slate-400">¥{t.amount?.toLocaleString()}</td>
                                <td className="py-1.5 px-2 text-slate-500 text-[10px]">{t.reason || "-"}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
