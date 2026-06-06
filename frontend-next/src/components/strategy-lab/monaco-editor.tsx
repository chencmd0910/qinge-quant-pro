"use client";

import { useState, useRef } from "react";
import Editor from "@monaco-editor/react";
import {
  Play,
  Save,
  RotateCcw,
  Terminal,
  CheckCircle2,
  Loader2,
  Code2,
  Settings,
} from "lucide-react";

const defaultCode = `class ETFRotationV6F(IndicatorStrategy):
    """ETF轮动策略 V6F - 量价因子

    因子组合:
    - volume_ratio (22%): 5日量比
    - money_flow (17%): 主力资金净流入
    - mom_5d (10%): 5日收益率
    - mom_10d (10%): 10日收益率
    - volatility_20d (5%): 20日波动率
    - daily_sharpe (5%): 20日日度夏普

    回测结果:
    - Annual Return: +19.57%
    - Max Drawdown: -5.00%
    - Sharpe Ratio: 2.500
    - Alpha: +16.9%
    """

    symbols = ["510300.SH", "510500.SH", "159915.SZ", "515080.SH"]
    lookback = 60
    rebalance_day = "friday"
    commission = 0.0003
    slippage = 0.001

    def setup(self):
        self.top_n = 1
        self.factor_weights = {
            "volume_ratio": 0.22,
            "money_flow": 0.17,
            "mom_5d": 0.10,
            "mom_10d": 0.10,
            "volatility_20d": 0.05,
            "daily_sharpe": 0.05,
        }

    def indicators(self, bars):
        """计算所有因子"""
        self.factors = {}
        for symbol in self.symbols:
            self.factors[symbol] = {
                "volume_ratio": self.calc_volume_ratio(bars[symbol], 5),
                "money_flow": self.calc_money_flow(bars[symbol], 5),
                "mom_5d": self.calc_returns(bars[symbol], 5),
                "mom_10d": self.calc_returns(bars[symbol], 10),
                "volatility_20d": self.calc_volatility(bars[symbol], 20),
                "daily_sharpe": self.calc_sharpe(bars[symbol], 20),
            }

    def generate_signal(self, bars):
        """生成交易信号"""
        if not self.is_rebalance_day():
            return None

        # 计算合成因子得分
        scores = {}
        for symbol in self.symbols:
            score = sum(
                weight * self.factors[symbol].get(factor, 0)
                for factor, weight in self.factor_weights.items()
            )
            scores[symbol] = score

        # 选取得分最高的ETF
        best = max(scores, key=scores.get)
        current = self.get_holding()

        signals = []
        if best != current:
            if current:
                signals.append(Signal(current, "SELL", strength=1.0))
            signals.append(Signal(best, "BUY", strength=1.0))

        return signals

    def is_rebalance_day(self):
        """判断是否为调仓日"""
        return self.current_date.weekday() == 4  # Friday
`;

export default function MonacoEditor() {
  const [code, setCode] = useState(defaultCode);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [showTerminal, setShowTerminal] = useState(true);

  const handleRun = () => {
    setIsRunning(true);
    setOutput([]);

    const steps = [
      "[INFO] Parsing strategy code...",
      "[INFO] Loading data: 510300.SH, 510500.SH, 159915.SZ, 515080.SH",
      "[INFO] Period: 2018-01-01 ~ 2026-06-05",
      "[INFO] Computing indicators...",
      "[INFO] Running backtest...",
      "[INFO] 2042 trading days processed",
      "[INFO] 108 trades executed",
      "[RESULT] Total Return: +20.78%",
      "[RESULT] Annual Return: +2.36%",
      "[RESULT] Max Drawdown: -59.16%",
      "[RESULT] Sharpe Ratio: 0.220",
      "[RESULT] Alpha: +2.85%",
      "[OK] Backtest complete!",
    ];

    steps.forEach((step, idx) => {
      setTimeout(() => {
        setOutput((prev) => [...prev, step]);
        if (idx === steps.length - 1) setIsRunning(false);
      }, (idx + 1) * 300);
    });
  };

  return (
    <div className="h-full flex flex-col bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Code2 size={14} className="text-blue-400" />
          <span className="text-xs font-semibold">Monaco Editor</span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
            strategy.py
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowTerminal(!showTerminal)}
            className={`p-1.5 rounded-md transition-colors ${
              showTerminal ? "bg-slate-700 text-slate-300" : "text-slate-500 hover:bg-slate-800"
            }`}
          >
            <Terminal size={14} />
          </button>
          <button className="p-1.5 rounded-md text-slate-500 hover:bg-slate-800 transition-colors">
            <Settings size={14} />
          </button>
          <button className="p-1.5 rounded-md text-slate-500 hover:bg-slate-800 transition-colors">
            <Save size={14} />
          </button>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="flex items-center gap-1.5 px-3 py-1.5 ml-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 rounded-md transition-colors"
          >
            {isRunning ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
            <span className="text-xs font-medium">Run</span>
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1" style={{ height: showTerminal ? "calc(100% - 200px)" : "100%" }}>
        <Editor
          defaultLanguage="python"
          defaultValue={defaultCode}
          theme="vs-dark"
          onChange={(value) => setCode(value || "")}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            padding: { top: 12, bottom: 12 },
            lineNumbers: "on",
            renderLineHighlight: "all",
            bracketPairColorization: { enabled: true },
            smoothScrolling: true,
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
          }}
        />
      </div>

      {/* Terminal */}
      {showTerminal && (
        <div className="h-[200px] border-t border-slate-800 bg-slate-950 flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800/50">
            <div className="flex items-center gap-2">
              <Terminal size={12} className="text-slate-500" />
              <span className="text-[10px] text-slate-500">Output</span>
            </div>
            <button
              onClick={() => setOutput([])}
              className="p-1 rounded hover:bg-slate-800 transition-colors"
            >
              <RotateCcw size={10} className="text-slate-600" />
            </button>
          </div>
          <div className="flex-1 overflow-auto p-3 font-mono text-[11px] leading-relaxed">
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
              <div className="flex items-center gap-2 text-blue-400">
                <Loader2 size={10} className="animate-spin" />
                <span>Running...</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
