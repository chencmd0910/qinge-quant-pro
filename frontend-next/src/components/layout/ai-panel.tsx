"use client";

import { useState } from "react";
import { Send, Bot, Sparkles, ChevronRight } from "lucide-react";

const insights = [
  {
    type: "alert",
    text: "FF4F 资金流策略 Alpha 转负，已自动标记 RETIRED",
    time: "2分钟前",
  },
  {
    type: "info",
    text: "V6F 量价策略连续30天 Alpha > 10%，稳定性优秀",
    time: "1小时前",
  },
  {
    type: "warning",
    text: "F5F 基本面策略进入 WATCHLIST，建议关注衰减趋势",
    time: "3小时前",
  },
];

export default function AIPanel() {
  const [input, setInput] = useState("");

  return (
    <aside className="w-[360px] border-l border-slate-800 bg-slate-950 flex flex-col">
      {/* Header */}
      <div className="h-16 border-b border-slate-800 flex items-center px-4 gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
          <Bot size={16} />
        </div>
        <div>
          <div className="text-sm font-semibold">AI Quant Agent</div>
          <div className="text-[10px] text-slate-500">GPT-4o Powered</div>
        </div>
      </div>

      {/* Insights */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles size={14} className="text-blue-400" />
          <span className="text-xs font-medium text-slate-300">AI Insights</span>
        </div>
        <div className="space-y-2">
          {insights.map((item, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors cursor-pointer group"
            >
              <div className="flex items-start gap-2">
                <div
                  className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                    item.type === "alert"
                      ? "bg-red-400"
                      : item.type === "warning"
                      ? "bg-amber-400"
                      : "bg-blue-400"
                  }`}
                />
                <div className="flex-1">
                  <p className="text-xs text-slate-300 leading-relaxed">{item.text}</p>
                  <span className="text-[10px] text-slate-600 mt-1 block">{item.time}</span>
                </div>
                <ChevronRight
                  size={12}
                  className="text-slate-600 group-hover:text-slate-400 transition-colors mt-0.5"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat */}
      <div className="flex-1 p-4 overflow-auto">
        <div className="space-y-4">
          <div className="flex gap-3">
            <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
              <Bot size={12} className="text-blue-400" />
            </div>
            <div className="bg-slate-900 rounded-lg p-3 text-xs text-slate-300 leading-relaxed max-w-[280px]">
              你好，我是青鳄 AI 量化助手。可以帮你分析策略、查看回测结果、监控风险。有什么需要？
            </div>
          </div>
        </div>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="帮我寻找夏普大于1.5的策略..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm
                       placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
          />
          <button className="w-9 h-9 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center transition-colors">
            <Send size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
}
