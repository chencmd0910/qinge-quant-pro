"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Play, RotateCcw } from "lucide-react";

interface Message {
  role: "user" | "agent";
  content: string;
  timestamp: string;
  actions?: string[];
}

const initialMessages: Message[] = [
  {
    role: "agent",
    content: "你好，我是青鳄 AI 研究助手。我可以帮你：\n\n• 生成和回测策略\n• 分析因子有效性\n• 运行 Walk Forward 验证\n• 监控 Alpha 衰减\n• 优化资金配置\n\n告诉我你想研究什么？",
    timestamp: "00:00",
  },
];

const quickActions = [
  "生成100个ETF轮动策略",
  "分析Top1策略的因子归因",
  "运行Walk Forward测试",
  "检查Alpha衰减状态",
  "优化资金配置权重",
];

export default function ResearchChat() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsRunning(true);

    // Simulate agent response
    setTimeout(() => {
      const agentMsg: Message = {
        role: "agent",
        content: `正在执行: "${input}"\n\n已完成:\n• 策略生成: 100个变体\n• 批量回测: 88个通过验证\n• Top1: V6F 量价_6F (Sharpe=2.500, Alpha=+16.9%)\n• 自动晋级: 2个ACTIVE, 2个WATCHLIST, 1个RETIRED`,
        timestamp: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
        actions: ["查看排行榜", "导出CSV", "启动模拟盘"],
      };
      setMessages((prev) => [...prev, agentMsg]);
      setIsRunning(false);
    }, 2000);
  };

  return (
    <div className="h-full flex flex-col bg-slate-900/60 border border-slate-800 rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center">
            <Sparkles size={14} />
          </div>
          <div>
            <div className="text-sm font-semibold">Research Chat</div>
            <div className="text-[10px] text-slate-500">AI-Powered Quant Research</div>
          </div>
        </div>
        <button className="p-1.5 rounded-md hover:bg-slate-800 transition-colors">
          <RotateCcw size={14} className="text-slate-500" />
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-auto p-5 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === "agent"
                  ? "bg-violet-500/20"
                  : "bg-blue-500/20"
              }`}
            >
              {msg.role === "agent" ? (
                <Bot size={13} className="text-violet-400" />
              ) : (
                <User size={13} className="text-blue-400" />
              )}
            </div>

            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 ${
                msg.role === "agent"
                  ? "bg-slate-800/60 border border-slate-700/50"
                  : "bg-blue-600/20 border border-blue-500/30"
              }`}
            >
              <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </div>

              {/* Action buttons */}
              {msg.actions && (
                <div className="flex flex-wrap gap-2 mt-3 pt-2 border-t border-slate-700/50">
                  {msg.actions.map((action) => (
                    <button
                      key={action}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-medium
                                 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-md
                                 hover:bg-blue-500/20 transition-colors"
                    >
                      <Play size={10} />
                      {action}
                    </button>
                  ))}
                </div>
              )}

              <div className="text-[9px] text-slate-600 mt-2">{msg.timestamp}</div>
            </div>
          </div>
        ))}

        {isRunning && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-violet-500/20 flex items-center justify-center">
              <Bot size={13} className="text-violet-400" />
            </div>
            <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" />
                  <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                  <div className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                </div>
                <span className="text-xs text-slate-400">正在执行...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="px-5 py-2 flex flex-wrap gap-2 border-t border-slate-800">
        {quickActions.map((action) => (
          <button
            key={action}
            onClick={() => setInput(action)}
            className="px-3 py-1.5 text-[10px] text-slate-400 bg-slate-800/60 border border-slate-700/50
                       rounded-md hover:border-slate-600 hover:text-slate-300 transition-colors"
          >
            {action}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="描述你想研究的策略... (Enter 发送, Shift+Enter 换行)"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-sm
                       placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50
                       transition-colors resize-none min-h-[80px]"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isRunning}
            className="w-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40
                       disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
