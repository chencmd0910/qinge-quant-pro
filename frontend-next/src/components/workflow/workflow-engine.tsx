"use client";

import { useState } from "react";
import {
  Play,
  RotateCcw,
  Cpu,
  BarChart3,
  ShieldCheck,
  Route,
  Trophy,
  CheckCircle2,
  Loader2,
  Circle,
  ChevronRight,
  Zap,
  Clock,
  Target,
} from "lucide-react";

type NodeStatus = "idle" | "running" | "done" | "error";

interface WorkflowNode {
  id: string;
  label: string;
  icon: any;
  description: string;
  status: NodeStatus;
  progress: number;
  result?: string;
  duration?: string;
}

const initialNodes: WorkflowNode[] = [
  {
    id: "generator",
    label: "Strategy Generator",
    icon: Cpu,
    description: "随机组合因子，生成100个策略变体",
    status: "idle",
    progress: 0,
  },
  {
    id: "backtest",
    label: "Batch Backtest",
    icon: BarChart3,
    description: "自动回测100个策略，计算收益/回撤/Sharpe",
    status: "idle",
    progress: 0,
  },
  {
    id: "validation",
    label: "Auto Validation",
    icon: ShieldCheck,
    description: "过滤过拟合、低Sharpe、负Alpha策略",
    status: "idle",
    progress: 0,
  },
  {
    id: "walkforward",
    label: "Walk Forward",
    icon: Route,
    description: "滚动窗口验证，确保策略在未见数据上有效",
    status: "idle",
    progress: 0,
  },
  {
    id: "tournament",
    label: "Tournament",
    icon: Trophy,
    description: "策略锦标赛，输出Top排行榜",
    status: "idle",
    progress: 0,
  },
];

const prompts = [
  "寻找年化>15%、回撤<10%的ETF轮动策略",
  "生成包含北向资金因子的多因子策略",
  "找出夏普>2.0的量价策略组合",
  "验证当前Top5策略的Alpha稳定性",
  "生成100个行业轮动策略并排名",
];

export default function WorkflowEngine() {
  const [nodes, setNodes] = useState<WorkflowNode[]>(initialNodes);
  const [prompt, setPrompt] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState<string | null>(null);

  const handleRun = () => {
    if (!prompt.trim() || isRunning) return;
    setIsRunning(true);
    setOutput(null);

    // Reset all nodes
    setNodes((prev) =>
      prev.map((n) => ({ ...n, status: "idle" as NodeStatus, progress: 0, result: undefined, duration: undefined }))
    );

    // Simulate sequential execution
    const steps = [
      { idx: 0, delay: 800, progress: 100, result: "100个策略生成完成", duration: "1.2s" },
      { idx: 1, delay: 1500, progress: 100, result: "88个通过, 12个失败", duration: "3.4s" },
      { idx: 2, delay: 1000, progress: 100, result: "88个验证通过", duration: "2.1s" },
      { idx: 3, delay: 1200, progress: 100, result: "3/3窗口通过, 一致性100%", duration: "4.8s" },
      { idx: 4, delay: 800, progress: 100, result: "Top1: V6F Sharpe=2.500 Alpha=+16.9%", duration: "0.5s" },
    ];

    let totalDelay = 0;
    steps.forEach((step) => {
      totalDelay += step.delay;

      // Start step
      setTimeout(() => {
        setNodes((prev) =>
          prev.map((n, i) => (i === step.idx ? { ...n, status: "running" as NodeStatus } : n))
        );

        // Animate progress
        let prog = 0;
        const interval = setInterval(() => {
          prog += Math.random() * 30 + 10;
          if (prog >= 100) {
            prog = 100;
            clearInterval(interval);
          }
          setNodes((prev) =>
            prev.map((n, i) => (i === step.idx ? { ...n, progress: Math.min(100, prog) } : n))
          );
        }, 100);
      }, totalDelay - step.delay);

      // Complete step
      setTimeout(() => {
        setNodes((prev) =>
          prev.map((n, i) =>
            i === step.idx
              ? { ...n, status: "done" as NodeStatus, progress: 100, result: step.result, duration: step.duration }
              : n
          )
        );
      }, totalDelay);
    });

    // Final output
    setTimeout(() => {
      setIsRunning(false);
      setOutput(
        `研究完成!\n\n` +
          `生成: 100个策略\n` +
          `回测: 100个 (88通过, 12失败)\n` +
          `验证: 88个通过\n` +
          `Walk Forward: 3/3窗口通过\n\n` +
          `Top 3:\n` +
          `  #1 V6F 量价_6F    Sharpe=2.500  Alpha=+16.9%\n` +
          `  #2 F5F 基本面_5F   Sharpe=1.594  Alpha=+12.6%\n` +
          `  #3 M5F 动量_5F    Sharpe=1.612  Alpha=+10.1%`
      );
    }, totalDelay + 500);
  };

  const handleReset = () => {
    setNodes(initialNodes);
    setIsRunning(false);
    setOutput(null);
  };

  const statusIcon = (status: NodeStatus) => {
    switch (status) {
      case "running":
        return <Loader2 size={16} className="text-blue-400 animate-spin" />;
      case "done":
        return <CheckCircle2 size={16} className="text-emerald-400" />;
      case "error":
        return <Circle size={16} className="text-red-400" />;
      default:
        return <Circle size={16} className="text-slate-600" />;
    }
  };

  const statusBorder = (status: NodeStatus) => {
    switch (status) {
      case "running":
        return "border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]";
      case "done":
        return "border-emerald-500/30";
      case "error":
        return "border-red-500/30";
      default:
        return "border-slate-700/50";
    }
  };

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center">
            <Zap size={16} />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Agent Workflow Engine</h1>
            <p className="text-xs text-slate-500">AI-Powered Research Pipeline</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 bg-slate-800 border border-slate-700 rounded-lg hover:border-slate-600 transition-colors"
          >
            <RotateCcw size={12} />
            Reset
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-4">
        {/* Left: Prompt + Workflow */}
        <div className="col-span-8 flex flex-col gap-4">
          {/* Prompt */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Target size={14} className="text-violet-400" />
              <span className="text-sm font-semibold">Research Prompt</span>
            </div>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="描述你想要的策略... 例如: 寻找年化>15%、回撤<10%的ETF轮动策略"
              className="w-full h-24 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-sm
                         placeholder:text-slate-600 focus:outline-none focus:border-violet-500/50 transition-colors resize-none"
            />
            <div className="flex items-center justify-between mt-3">
              <div className="flex flex-wrap gap-1.5">
                {prompts.slice(0, 3).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPrompt(p)}
                    className="px-2.5 py-1 text-[10px] text-slate-500 bg-slate-800 border border-slate-700/50 rounded-md hover:border-slate-600 hover:text-slate-300 transition-colors"
                  >
                    {p}
                  </button>
                ))}
              </div>
              <button
                onClick={handleRun}
                disabled={!prompt.trim() || isRunning}
                className="flex items-center gap-1.5 px-5 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                {isRunning ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
                <span className="text-sm font-medium">{isRunning ? "Running..." : "Run Workflow"}</span>
              </button>
            </div>
          </div>

          {/* Workflow Nodes */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 flex-1">
            <div className="flex items-center gap-2 mb-5">
              <Zap size={14} className="text-amber-400" />
              <span className="text-sm font-semibold">Pipeline</span>
              {isRunning && (
                <span className="ml-auto text-[10px] text-blue-400 flex items-center gap-1">
                  <Loader2 size={10} className="animate-spin" />
                  Executing...
                </span>
              )}
            </div>

            <div className="space-y-3">
              {nodes.map((node, idx) => (
                <div key={node.id}>
                  <div
                    className={`
                      relative p-4 rounded-xl border transition-all duration-300
                      ${statusBorder(node.status)}
                      ${node.status === "idle" ? "bg-slate-800/30" : "bg-slate-800/60"}
                    `}
                  >
                    {/* Progress bar background */}
                    {node.status === "running" && (
                      <div className="absolute inset-0 rounded-xl overflow-hidden">
                        <div
                          className="h-full bg-blue-500/5 transition-all duration-200"
                          style={{ width: `${node.progress}%` }}
                        />
                      </div>
                    )}

                    <div className="relative flex items-center gap-4">
                      {/* Step number */}
                      <div
                        className={`
                          w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0
                          ${node.status === "done"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : node.status === "running"
                            ? "bg-blue-500/20 text-blue-400"
                            : "bg-slate-700 text-slate-500"
                          }
                        `}
                      >
                        {idx + 1}
                      </div>

                      {/* Icon */}
                      <div
                        className={`
                          w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                          ${node.status === "done"
                            ? "bg-emerald-500/10"
                            : node.status === "running"
                            ? "bg-blue-500/10"
                            : "bg-slate-700/50"
                          }
                        `}
                      >
                        <node.icon
                          size={18}
                          className={
                            node.status === "done"
                              ? "text-emerald-400"
                              : node.status === "running"
                              ? "text-blue-400"
                              : "text-slate-500"
                          }
                        />
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{node.label}</span>
                          {statusIcon(node.status)}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">{node.description}</p>
                      </div>

                      {/* Progress / Result */}
                      <div className="text-right flex-shrink-0 w-32">
                        {node.status === "running" && (
                          <div>
                            <div className="text-xs font-mono text-blue-400">{Math.round(node.progress)}%</div>
                            <div className="mt-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-500 rounded-full transition-all duration-200"
                                style={{ width: `${node.progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                        {node.status === "done" && (
                          <div>
                            <div className="text-[11px] text-emerald-400 font-medium">{node.result}</div>
                            {node.duration && (
                              <div className="flex items-center gap-1 justify-end mt-0.5">
                                <Clock size={9} className="text-slate-600" />
                                <span className="text-[9px] text-slate-600">{node.duration}</span>
                              </div>
                            )}
                          </div>
                        )}
                        {node.status === "idle" && (
                          <span className="text-[10px] text-slate-600">Waiting...</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Connector */}
                  {idx < nodes.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ChevronRight
                        size={14}
                        className={`rotate-90 ${
                          node.status === "done" ? "text-emerald-500/50" : "text-slate-700"
                        }`}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Results */}
        <div className="col-span-4 flex flex-col gap-4">
          {/* Stats */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <div className="text-xs font-semibold mb-3">Execution Stats</div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "Generated", value: "100", color: "text-blue-400" },
                { label: "Validated", value: "88", color: "text-emerald-400" },
                { label: "Filtered", value: "12", color: "text-red-400" },
                { label: "Duration", value: "12.0s", color: "text-amber-400" },
              ].map((s) => (
                <div key={s.label} className="p-2.5 rounded-lg bg-slate-800/60 text-center">
                  <div className={`text-lg font-bold font-mono ${s.color}`}>{s.value}</div>
                  <div className="text-[9px] text-slate-500">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Output */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1">
            <div className="text-xs font-semibold mb-3">Output</div>
            {output ? (
              <pre className="text-[11px] text-slate-300 leading-relaxed whitespace-pre-wrap font-mono">
                {output}
              </pre>
            ) : (
              <div className="flex flex-col items-center justify-center h-40 text-slate-600">
                <Zap size={24} className="mb-2 opacity-30" />
                <span className="text-xs">运行工作流查看结果</span>
              </div>
            )}
          </div>

          {/* Top 3 */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <div className="text-xs font-semibold mb-3">Top 3 Candidates</div>
            <div className="space-y-2">
              {[
                { rank: 1, name: "V6F 量价", sharpe: "2.500", alpha: "+16.9%" },
                { rank: 2, name: "F5F 基本面", sharpe: "1.594", alpha: "+12.6%" },
                { rank: 3, name: "M5F 动量", sharpe: "1.612", alpha: "+10.1%" },
              ].map((s) => (
                <div key={s.rank} className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/40">
                  <div className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold ${
                    s.rank === 1 ? "bg-amber-500/20 text-amber-400" : "bg-slate-700 text-slate-500"
                  }`}>
                    {s.rank}
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-medium">{s.name}</div>
                    <div className="text-[10px] text-slate-500">S:{s.sharpe}</div>
                  </div>
                  <span className="text-xs font-mono text-emerald-400">{s.alpha}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
