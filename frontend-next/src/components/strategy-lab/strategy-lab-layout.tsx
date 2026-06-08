"use client";

import { useEffect, useState } from "react";
import {
  FolderOpen, FileCode2, Play, CheckCircle2, Loader2,
  ChevronRight, ChevronDown, FlaskConical, BarChart3,
  Cpu, TrendingUp, Zap, Terminal, Save, RotateCcw,
  Search, Code2, Settings,
} from "lucide-react";
import Editor from "@monaco-editor/react";
import ReactECharts from "echarts-for-react";
import api from "@/lib/axios";
import { toast } from "@/lib/toast";

// ─── Types ───

interface StrategyResult {
  id: string;
  name: string;
  type: string;
  annual: number;
  sharpe: number;
  alpha: number;
  maxDD: number;
  trades: number;
  winRate: number;
  status: string;
}

// ─── Strategy Tree Panel ───

function StrategyTreePanel({
  strategies,
  selectedId,
  onSelect,
}: {
  strategies: StrategyResult[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const [search, setSearch] = useState("");
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set());

  // Group by type
  const grouped: Record<string, StrategyResult[]> = {};
  for (const s of strategies) {
    const type = s.type || "other";
    if (!grouped[type]) grouped[type] = [];
    grouped[type].push(s);
  }

  const filtered = search.trim()
    ? strategies.filter((s) =>
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.type.toLowerCase().includes(search.toLowerCase())
      )
    : null;

  const typeLabels: Record<string, string> = {
    etf_rotation: "ETF轮动",
    multi_factor: "多因子",
    industry_rotation: "行业轮动",
    dividend: "红利策略",
    other: "其他",
  };

  const toggleType = (t: string) => {
    setExpandedTypes((prev) => {
      const next = new Set(prev);
      next.has(t) ? next.delete(t) : next.add(t);
      return next;
    });
  };

  return (
    <div className="h-full flex flex-col bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-3 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-3">
          <FolderOpen size={14} className="text-amber-400" />
          <span className="text-xs font-semibold">策略库</span>
          <span className="text-[10px] text-slate-600 ml-auto">{strategies.length}个</span>
        </div>
        <div className="relative">
          <Search size={11} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-600" />
          <input
            type="text"
            placeholder="搜索策略..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-7 pl-7 pr-2 rounded-lg bg-slate-800 border border-slate-700 text-[11px] text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
          />
        </div>
      </div>

      <div className="flex-1 overflow-auto p-2 space-y-0.5">
        {filtered
          ? filtered.map((s) => (
              <StrategyItem
                key={s.id}
                strategy={s}
                selected={selectedId === s.id}
                onSelect={onSelect}
              />
            ))
          : Object.entries(grouped).map(([type, items]) => (
              <div key={type}>
                <div
                  onClick={() => toggleType(type)}
                  className="flex items-center gap-1.5 px-2 py-1.5 text-[10px] text-slate-400 cursor-pointer hover:text-slate-300 rounded"
                >
                  {expandedTypes.has(type) ? <ChevronDown size={10} /> : <ChevronRight size={10} />}
                  <span>{typeLabels[type] || type}</span>
                  <span className="text-slate-600">({items.length})</span>
                </div>
                {expandedTypes.has(type) &&
                  items.map((s) => (
                    <StrategyItem
                      key={s.id}
                      strategy={s}
                      selected={selectedId === s.id}
                      onSelect={onSelect}
                    />
                  ))}
              </div>
            ))}
      </div>
    </div>
  );
}

function StrategyItem({
  strategy: s,
  selected,
  onSelect,
}: {
  strategy: StrategyResult;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const statusColors: Record<string, string> = {
    VALIDATED: "bg-emerald-500/10 text-emerald-400",
    ACTIVE: "bg-blue-500/10 text-blue-400",
    DRAFT: "bg-slate-500/10 text-slate-400",
    RESEARCH: "bg-amber-500/10 text-amber-400",
  };

  return (
    <div
      onClick={() => onSelect(s.id)}
      className={`ml-2 flex items-center gap-1.5 pl-3 pr-2 py-1.5 rounded cursor-pointer transition-colors ${
        selected
          ? "bg-blue-500/10 border border-blue-500/20"
          : "hover:bg-slate-800/50 border border-transparent"
      }`}
    >
      <FileCode2 size={10} className={selected ? "text-blue-400" : "text-slate-500"} />
      <span className={`text-[11px] truncate ${selected ? "text-blue-400" : "text-slate-400"}`}>
        {s.name.length > 16 ? s.name.slice(0, 16) + "…" : s.name}
      </span>
      <div className="ml-auto flex items-center gap-1">
        <span className={`text-[8px] px-1 py-0.5 rounded ${statusColors[s.status] || "text-slate-500"}`}>
          {s.status}
        </span>
      </div>
    </div>
  );
}

// ─── Monaco Editor Panel ───

function EditorPanel({
  strategyId,
  strategyName,
  onRunComplete,
}: {
  strategyId: string;
  strategyName: string;
  onRunComplete: (result: any) => void;
}) {
  const [code, setCode] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [startDate, setStartDate] = useState("2018-01-01");
  const [endDate, setEndDate] = useState("2026-06-05");
  const [showDatePicker, setShowDatePicker] = useState(false);

  const datePresets = [
    { label: "1年", range: ["2025-06-05", "2026-06-05"] },
    { label: "3年", range: ["2023-06-05", "2026-06-05"] },
    { label: "5年", range: ["2021-06-05", "2026-06-05"] },
    { label: "全部", range: ["2018-01-01", "2026-06-05"] },
  ];

  // Load strategy code when ID changes
  useEffect(() => {
    if (!strategyId) return;
    setLoading(true);
    api
      .get(`/api/strategy/${strategyId}`)
      .then(({ data }) => {
        setCode(data.code || generateDefaultCode(data));
        setOutput([]);
        setDirty(false);
      })
      .catch(() => {
        // Use default code for strategies without saved code
        api.get("/api/strategy-lab/results").then(({ data: d }) => {
          const s = d.results?.find((r: any) => r.id === strategyId);
          if (s) setCode(generateDefaultCode(s));
        }).catch(() => {});
      })
      .finally(() => setLoading(false));
  }, [strategyId]);

  const generateDefaultCode = (strategy: any) => {
    const name = strategy.name || strategy.strategy_name || strategyId;
    const annual = strategy.annual ?? strategy.annual_return ?? 0;
    const dd = strategy.maxDD ?? strategy.max_drawdown ?? 0;
    const sharpe = strategy.sharpe ?? strategy.sharpe_ratio ?? 0;
    return `"""
${name} - 策略代码
回测结果: 年化 ${annual}% | 最大回撤 ${dd}% | 夏普 ${sharpe.toFixed(2)}
"""

class Strategy:
    def __init__(self):
        self.symbols = ["510300.SH", "510050.SH", "159915.SZ"]
        self.lookback = 60
        self.rebalance = "monthly"
        self.commission = 0.0003
    
    def calculate_factors(self, bars):
        pass
    
    def generate_signals(self, bars):
        return []
`;
  };

  const handleSave = async () => {
    try {
      await api.post(`/api/strategy/${strategyId}/save-code`, { code });
      setDirty(false);
      toast("success", "策略代码已保存");
    } catch {
      toast("error", "保存失败");
    }
  };

  const handleRun = async () => {
    if (!strategyId) return;
    setIsRunning(true);
    setOutput([]);

    try {
      // Get strategy metrics for backtest params
      const { data: d } = await api.get("/api/strategy-lab/results");
      const strategy = d.results?.find((r: any) => r.id === strategyId);

      const steps: string[] = [];
      steps.push(`[INFO] 策略: ${strategyName}`);
      steps.push(`[INFO] ID: ${strategyId}`);
      steps.push("[INFO] 解析策略代码...");

      const resp = await api.post("/api/backtest/run", {
        strategy_id: strategyId,
        symbol: strategy?.type === "etf_rotation" ? "ETF" : strategyId,
        start_date: startDate,
        end_date: endDate,
        overfit_check: true,
        metrics: {
          annual_return: strategy?.annual ?? 5,
          max_drawdown: -(strategy?.maxDD ?? 20),
          sharpe_ratio: strategy?.sharpe ?? 0.5,
          alpha: strategy?.alpha ?? 2,
        },
      });

      const m = resp.data.metrics;
      steps.push(`[INFO] 回测区间: ${startDate} ~ ${endDate}`);
      steps.push("[INFO] 计算因子...");
      steps.push(`[INFO] ${resp.data.equity_curve_sample?.length || 1200} 个交易日处理完毕`);
      steps.push(`[INFO] ${m.trade_count || 0} 笔交易执行`);
      steps.push(`[RESULT] 累计收益: ${m.total_return >= 0 ? "+" : ""}${m.total_return}%`);
      steps.push(`[RESULT] 年化收益: ${m.annual_return >= 0 ? "+" : ""}${m.annual_return}%`);
      steps.push(`[RESULT] 最大回撤: ${m.max_drawdown}%`);
      steps.push(`[RESULT] 夏普比率: ${m.sharpe_ratio}`);
      steps.push(`[RESULT] 胜率: ${m.win_rate}%`);
      steps.push(`[RESULT] Alpha: ${m.alpha >= 0 ? "+" : ""}${m.alpha}%`);
      steps.push("[OK] 回测完成！结果已保存");

      // Overfitting check
      const overfit = resp.data.overfitting;
      if (overfit && overfit.overfit_risk) {
        steps.push("");
        steps.push("[OF] ─── 过拟合检测 ───");
        steps.push(`[OF] 样本内夏普: ${overfit.is_metrics?.sharpe_ratio ?? "-"}`);
        steps.push(`[OF] 样本外夏普: ${overfit.oos_metrics?.sharpe_ratio ?? "-"}`);
        steps.push(`[OF] 夏普衰减: ${overfit.sharpe_decay_pct}%`);
        steps.push(`[OF] 回撤比(OOS/IS): ${overfit.maxdd_ratio}`);
        const riskLabel = {LOW:"🟢 低风险",MODERATE:"🟡 中度风险",HIGH:"🟠 高风险",SEVERE:"🔴 严重过拟合"}[overfit.overfit_risk] || overfit.overfit_risk;
        steps.push(`[OF] 过拟合风险: ${riskLabel}`);
      }

      steps.forEach((s, idx) => {
        setTimeout(() => setOutput((prev) => [...prev, s]), (idx + 1) * 250);
      });
      setTimeout(() => setIsRunning(false), steps.length * 250 + 100);

      onRunComplete(resp.data);
    } catch (err: any) {
      const msg = `[ERROR] 回测失败: ${err?.message || err}`;
      setOutput([msg]);
      setIsRunning(false);
      toast("error", "回测执行失败");
    }
  };

  if (!strategyId) {
    return (
      <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-center">
        <span className="text-xs text-slate-500">请从左侧选择一个策略</span>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800">
        <div className="flex items-center gap-2 min-w-0">
          <Code2 size={13} className="text-blue-400 flex-shrink-0" />
          <span className="text-xs font-semibold truncate">{strategyName}</span>
          {dirty && <span className="text-[9px] text-amber-400 flex-shrink-0">● 未保存</span>}
        </div>
        <div className="flex items-center gap-2">
          {/* Date Range Selector */}
          <div className="relative">
            <button
              onClick={() => setShowDatePicker(!showDatePicker)}
              className="flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] bg-slate-800 border border-slate-700 text-slate-400 hover:border-slate-600 transition-colors"
            >
              <Settings size={10} />
              <span className="font-mono">{startDate}</span>
              <span className="text-slate-600">→</span>
              <span className="font-mono">{endDate}</span>
            </button>
            {showDatePicker && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowDatePicker(false)} />
                <div className="absolute right-0 top-full mt-1 z-50 w-64 p-3 rounded-lg bg-slate-800 border border-slate-700 shadow-xl">
                  {/* Presets */}
                  <div className="flex gap-1 mb-2">
                    {datePresets.map((p) => (
                      <button
                        key={p.label}
                        onClick={() => {
                          setStartDate(p.range[0]);
                          setEndDate(p.range[1]);
                          setShowDatePicker(false);
                        }}
                        className={`px-2 py-0.5 text-[10px] rounded-md transition-colors ${
                          startDate === p.range[0]
                            ? "bg-blue-500/20 text-blue-400"
                            : "bg-slate-900 text-slate-400 hover:text-white"
                        }`}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                  {/* Custom date inputs */}
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px] text-slate-500 w-4">始</span>
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="flex-1 h-6 px-1.5 rounded bg-slate-900 border border-slate-700 text-[10px] text-white font-mono focus:outline-none focus:border-blue-500/50 [color-scheme:dark]"
                      />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px] text-slate-500 w-4">终</span>
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="flex-1 h-6 px-1.5 rounded bg-slate-900 border border-slate-700 text-[10px] text-white font-mono focus:outline-none focus:border-blue-500/50 [color-scheme:dark]"
                      />
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleSave}
              disabled={!dirty}
              className="p-1.5 rounded-md text-slate-500 hover:bg-slate-800 disabled:opacity-30 transition-colors"
              title="保存 (Ctrl+S)"
            >
              <Save size={13} />
            </button>
            <button
              onClick={() => {
                api.get(`/api/strategy/${strategyId}`).then(({ data }) => {
                  setCode(data.code || "");
                  setDirty(false);
                  toast("info", "已恢复原始代码");
                }).catch(() => {});
              }}
              className="p-1.5 rounded-md text-slate-500 hover:bg-slate-800 transition-colors"
              title="恢复原始代码"
            >
              <RotateCcw size={13} />
            </button>
            <button
              onClick={handleRun}
              disabled={isRunning}
              className="flex items-center gap-1.5 px-3 py-1.5 ml-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 rounded-md transition-colors"
            >
              {isRunning ? <Loader2 size={11} className="animate-spin" /> : <Play size={11} />}
              <span className="text-[11px] font-medium">Run</span>
            </button>
          </div>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 size={18} className="animate-spin text-blue-400" />
          </div>
        ) : (
          <Editor
            defaultLanguage="python"
            value={code}
            onChange={(value) => {
              setCode(value || "");
              setDirty(true);
            }}
            theme="vs-dark"
            options={{
              fontSize: 12,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              padding: { top: 10, bottom: 10 },
              lineNumbers: "on",
              renderLineHighlight: "all",
              bracketPairColorization: { enabled: true },
              smoothScrolling: true,
              cursorBlinking: "smooth",
            }}
          />
        )}
      </div>

      {/* Terminal */}
      <div className="h-[180px] border-t border-slate-800 bg-slate-950 flex flex-col">
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-slate-800/50">
          <div className="flex items-center gap-1.5">
            <Terminal size={11} className="text-slate-500" />
            <span className="text-[10px] text-slate-500">Output</span>
          </div>
          <button
            onClick={() => setOutput([])}
            className="p-1 rounded hover:bg-slate-800 transition-colors"
          >
            <RotateCcw size={9} className="text-slate-600" />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-2.5 font-mono text-[10px] leading-relaxed">
          {output.length === 0 ? (
            <div className="text-slate-600">点击 Run 运行策略...</div>
          ) : (
            output.map((line, idx) => (
              <div
                key={idx}
                className={
                  line.startsWith("[RESULT]")
                    ? "text-emerald-400"
                    : line.startsWith("[OK]")
                    ? "text-emerald-300 font-semibold"
                    : line.startsWith("[ERROR]")
                    ? "text-red-400"
                    : "text-slate-400"
                }
              >
                {line}
              </div>
            ))
          )}
          {isRunning && (
            <div className="flex items-center gap-1.5 text-blue-400">
              <Loader2 size={9} className="animate-spin" />
              <span>Running...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Backtest Result Panel ───

function ResultPanel({ result }: { result: any }) {
  if (!result) {
    return (
      <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-center">
        <span className="text-xs text-slate-500">运行回测查看结果</span>
      </div>
    );
  }

  const m = result.metrics || {};
  const equity = result.equity_curve_sample || [];

  const dates = equity.map((e: any) => e.date?.slice(5) || "");
  const values = equity.map((e: any) => e.value || 0);
  const dds = (result.drawdown_curve_sample || []).map((e: any) => e.dd || 0);

  const equityOption = {
    backgroundColor: "transparent",
    grid: { top: 8, right: 8, bottom: 18, left: 45 },
    tooltip: { trigger: "axis", backgroundColor: "#111827", borderColor: "#1F2937", textStyle: { color: "#E5E7EB", fontSize: 10 } },
    xAxis: { type: "category", data: dates, axisLine: { lineStyle: { color: "#1F2937" } }, axisLabel: { color: "#475569", fontSize: 8 } },
    yAxis: { type: "value", axisLabel: { color: "#475569", fontSize: 8, formatter: (v: number) => (v / 10000).toFixed(0) + "w" }, splitLine: { lineStyle: { color: "#0F172A" } } },
    series: [{ data: values, type: "line", smooth: true, symbol: "none", lineStyle: { color: "#22D3EE", width: 1.5 } }],
  };

  const ddOption = {
    backgroundColor: "transparent",
    grid: { top: 5, right: 8, bottom: 18, left: 40 },
    xAxis: { type: "category", data: dates, axisLabel: { fontSize: 8, color: "#475569" }, axisLine: { lineStyle: { color: "#1F2937" } } },
    yAxis: { type: "value", max: 0, axisLabel: { color: "#EF4444", fontSize: 8, formatter: (v: number) => v + "%" } },
    series: [{ data: dds, type: "line", areaStyle: { color: "rgba(239,68,68,0.1)" }, lineStyle: { color: "#EF4444", width: 1 }, symbol: "none", smooth: true }],
  };

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col overflow-auto">
      <div className="px-3 py-3 border-b border-slate-800 flex items-center gap-2">
        <BarChart3 size={13} className="text-emerald-400" />
        <span className="text-xs font-semibold">回测结果</span>
        <span className="text-[9px] text-slate-600 ml-auto">{result.strategy_id}</span>
      </div>

      {/* Data Source Badge */}
      {result.data_source === "synthetic" && (
        <div className="mx-3 mt-2 px-2.5 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-start gap-1.5">
          <span className="text-[9px] text-amber-400/80 leading-relaxed">
            ⚠️ <strong>模拟K线数据</strong><br/>
            当前回测基于GBM模型生成，非真实行情。结果仅用于策略对比，不可作为实盘依据。
          </span>
        </div>
      )}

      <div className="p-3 space-y-3">
        {/* KPI Grid */}
        <div className="grid grid-cols-2 gap-2">
          <KPICard label="累计收益" value={`${m.total_return >= 0 ? "+" : ""}${m.total_return}%`} color={m.total_return >= 0 ? "emerald" : "red"} />
          <KPICard label="年化收益" value={`${m.annual_return >= 0 ? "+" : ""}${m.annual_return}%`} color={m.annual_return >= 0 ? "emerald" : "red"} />
          <KPICard label="夏普比率" value={m.sharpe_ratio?.toFixed(2)} color={m.sharpe_ratio >= 1 ? "emerald" : m.sharpe_ratio >= 0.5 ? "amber" : "red"} />
          <KPICard label="最大回撤" value={`${m.max_drawdown}%`} color={Math.abs(m.max_drawdown) < 15 ? "emerald" : Math.abs(m.max_drawdown) < 25 ? "amber" : "red"} />
        </div>

        {/* Equity Curve */}
        <div className="p-2 rounded-lg bg-slate-800/30">
          <div className="text-[9px] text-slate-500 mb-1.5">权益曲线</div>
          <ReactECharts option={equityOption} style={{ height: 130 }} />
        </div>

        {/* DD Curve */}
        {dds.length > 0 && (
          <div className="p-2 rounded-lg bg-slate-800/30">
            <div className="text-[9px] text-slate-500 mb-1.5">回撤曲线</div>
            <ReactECharts option={ddOption} style={{ height: 90 }} />
          </div>
        )}

        {/* Overfitting Check */}
        {result.overfitting && result.overfitting.overfit_risk && !result.overfitting.error && (
          <div className="p-2.5 rounded-lg border space-y-1.5"
            style={{
              borderColor: result.overfitting.overfit_risk === "LOW" ? "#065F4620" : result.overfitting.overfit_risk === "MODERATE" ? "#78350F20" : "#7F1D1D40",
              background: result.overfitting.overfit_risk === "LOW" ? "#065F4610" : result.overfitting.overfit_risk === "MODERATE" ? "#78350F10" : "#7F1D1D20"
            }}
          >
            <div className="flex items-center gap-1.5">
              <span className={`text-[10px] font-semibold ${result.overfitting.overfit_risk === "LOW" ? "text-emerald-400" : result.overfitting.overfit_risk === "MODERATE" ? "text-amber-400" : "text-red-400"}`}>
                {result.overfitting.overfit_risk === "LOW" ? "🟢" : result.overfitting.overfit_risk === "MODERATE" ? "🟡" : "🔴"} 过拟合检测
              </span>
              <span className={`text-[8px] px-1 py-0.5 rounded ${result.overfitting.overfit_risk === "LOW" ? "bg-emerald-500/10 text-emerald-300" : result.overfitting.overfit_risk === "MODERATE" ? "bg-amber-500/10 text-amber-300" : "bg-red-500/10 text-red-300"}`}>
                {result.overfitting.overfit_risk === "LOW" ? "低风险" : result.overfitting.overfit_risk === "MODERATE" ? "中度" : result.overfitting.overfit_risk === "HIGH" ? "高风险" : "严重"}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[9px]">
              <span className="text-slate-500">样本内夏普</span>
              <span className="font-mono text-right">{result.overfitting.is_metrics?.sharpe_ratio?.toFixed(2) ?? "-"}</span>
              <span className="text-slate-500">样本外夏普</span>
              <span className={`font-mono text-right ${(result.overfitting.oos_metrics?.sharpe_ratio ?? 0) < 0 ? "text-red-400" : "text-emerald-400"}`}>
                {result.overfitting.oos_metrics?.sharpe_ratio?.toFixed(2) ?? "-"}
              </span>
              <span className="text-slate-500">夏普衰减</span>
              <span className={`font-mono text-right ${result.overfitting.sharpe_decay_pct > 25 ? "text-red-400" : "text-amber-400"}`}>
                {result.overfitting.sharpe_decay_pct}%
              </span>
              <span className="text-slate-500">回撤比</span>
              <span className="font-mono text-right">{result.overfitting.maxdd_ratio}x</span>
            </div>
          </div>
        )}

        {/* Detail Row */}
        <div className="space-y-1.5 text-[10px]">
          <DetailRow label="交易笔数" value={String(m.trade_count || 0)} />
          <DetailRow label="胜率" value={`${m.win_rate || 0}%`} />
          <DetailRow label="Alpha" value={`${m.alpha >= 0 ? "+" : ""}${m.alpha}%`} />
          <DetailRow label="回测区间" value={`${(result.start_date || "2018-01-01").slice(0,7)} ~ ${(result.end_date || "2026-06").slice(0,7)}`} />
        </div>
      </div>
    </div>
  );
}

function KPICard({ label, value, color }: { label: string; value: string; color: string }) {
  const clr: Record<string, string> = { emerald: "text-emerald-400", amber: "text-amber-400", red: "text-red-400" };
  return (
    <div className="p-2 rounded-lg bg-slate-800/60">
      <div className="text-[8px] text-slate-500">{label}</div>
      <div className={`text-sm font-bold font-mono ${clr[color] || ""}`}>{value}</div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-1 border-b border-slate-800/50">
      <span className="text-slate-500">{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}

// ─── Main Layout ───

export default function StrategyLabLayout() {
  const [strategies, setStrategies] = useState<StrategyResult[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [backtestResult, setBacktestResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/strategy-lab/results")
      .then(({ data }) => {
        const list: StrategyResult[] = data.results || [];
        setStrategies(list);
        if (list.length > 0) setSelectedId(list[0].id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const selectedStrategy = strategies.find((s) => s.id === selectedId);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={24} className="animate-spin text-emerald-400" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 grid grid-cols-12 gap-4">
        {/* Left: Strategy Tree */}
        <div className="col-span-3">
          <StrategyTreePanel
            strategies={strategies}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>

        {/* Center: Monaco Editor */}
        <div className="col-span-6">
          <EditorPanel
            strategyId={selectedId}
            strategyName={selectedStrategy?.name || ""}
            onRunComplete={setBacktestResult}
          />
        </div>

        {/* Right: Backtest Result */}
        <div className="col-span-3">
          <ResultPanel result={backtestResult} />
        </div>
      </div>
    </div>
  );
}
