"use client";

import { useState } from "react";
import {
  Cpu,
  Route,
  ShieldCheck,
  CheckCircle,
  Factory,
  Shield,
  FlaskConical,
  BarChart3,
  Bot,
} from "lucide-react";

const agents = [
  { name: "Strategy Generator", icon: Cpu, desc: "自动组合因子生成策略", active: true },
  { name: "Walk Forward", icon: Route, desc: "滚动窗口验证" },
  { name: "Reality Check", icon: ShieldCheck, desc: "OOS + Monte Carlo" },
  { name: "Validator", icon: CheckCircle, desc: "自动过滤不合格策略" },
  { name: "Alpha Factory", icon: Factory, desc: "ACTIVE/WATCH/RETIRED" },
  { name: "Risk Engine", icon: Shield, desc: "仓位管理 + 回撤控制" },
  { name: "Factor Lab", icon: FlaskConical, desc: "因子研究与归因" },
  { name: "Tournament", icon: BarChart3, desc: "策略锦标赛排名" },
  { name: "AI Agent", icon: Bot, desc: "自然语言研究助手" },
];

export default function AgentPool() {
  const [selected, setSelected] = useState(0);

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
        <div className="w-6 h-6 rounded-md bg-blue-500/10 flex items-center justify-center">
          <Bot size={12} className="text-blue-400" />
        </div>
        <div>
          <div className="text-xs font-semibold">Agent Pool</div>
          <div className="text-[9px] text-slate-500">{agents.length} agents</div>
        </div>
      </div>

      <div className="flex-1 space-y-1.5 overflow-auto">
        {agents.map((agent, idx) => (
          <div
            key={agent.name}
            onClick={() => setSelected(idx)}
            className={`
              p-3 rounded-lg cursor-pointer transition-all duration-150
              ${selected === idx
                ? "bg-blue-500/10 border border-blue-500/30"
                : "bg-slate-800/40 border border-transparent hover:bg-slate-800/70"
              }
            `}
          >
            <div className="flex items-center gap-2">
              <agent.icon
                size={14}
                className={selected === idx ? "text-blue-400" : "text-slate-500"}
              />
              <span className={`text-xs font-medium ${
                selected === idx ? "text-blue-300" : "text-slate-300"
              }`}>
                {agent.name}
              </span>
            </div>
            <p className="text-[10px] text-slate-500 mt-1.5 leading-relaxed">
              {agent.desc}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-slate-800">
        <div className="flex items-center gap-2 text-[10px] text-slate-500">
          <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
          All agents online
        </div>
      </div>
    </div>
  );
}
