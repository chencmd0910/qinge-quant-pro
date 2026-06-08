"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Sparkles, Loader2 } from "lucide-react";
import api from "@/lib/axios";

interface Message {
  role: "user" | "agent";
  content: string;
  timestamp: string;
  tool?: string;
}

const WELCOME: Message = {
  role: "agent",
  content: "你好老大，我是布布 🐊\n\n我能直接帮你：\n• ⚡ 回测策略 —「回测茅台」\n• 💼 查持仓 —「看看持仓」\n• 📊 仪表盘 —「总览」\n• 💹 行情数据 —「茅台最近走势」\n• 🧪 策略列表 —「所有策略」\n• 🏭 Alpha工厂\n• 🚨 风险警报\n• 🛡️ 风险指标\n\n跟我说你想做什么！",
  timestamp: "",
};

const QUICK_ACTIONS = [
  "📊 仪表盘总览",
  "💼 看看持仓",
  "⚡ 回测茅台",
  "💹 茅台最近行情",
  "🧪 所有策略排名",
  "🏭 Alpha工厂",
];

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    const userMsg: Message = {
      role: "user",
      content: msg,
      timestamp: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await api.post("/api/ai/chat", {
        message: msg,
        history: messages.slice(-10).map((m) => ({ role: m.role, content: m.content })),
      });

      const agentMsg: Message = {
        role: "agent",
        content: data.reply,
        timestamp: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
        tool: data.tool,
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch (e: unknown) {
      const errMsg: Message = {
        role: "agent",
        content: `❌ 后端服务异常: ${e instanceof Error ? e.message : "请确认 :8000 已启动"}`,
        timestamp: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      {/* Header */}
      <div className="flex items-center px-4 py-2.5 border-b" style={{ borderColor: "var(--border-color)" }}>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-400 flex items-center justify-center">
            <Sparkles size={12} className="text-slate-900" />
          </div>
          <div>
            <div className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>AI 对话 · 布布</div>
            <div className="text-[9px] text-slate-500">自然语言 → MCP 量化工具</div>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
          <span className="text-[9px] text-emerald-400">在线</span>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-auto p-4 space-y-3">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.role === "agent" ? "bg-emerald-500/20" : "bg-blue-500/20"
            }`}>
              {msg.role === "agent" ? (
                <Bot size={11} className="text-emerald-400" />
              ) : (
                <User size={11} className="text-blue-400" />
              )}
            </div>
            <div className={`max-w-[85%] rounded-lg px-3 py-2 ${
              msg.role === "agent"
                ? "bg-slate-800/60 border border-slate-700/50"
                : "bg-blue-600/15 border border-blue-500/20"
            }`}>
              <div className="text-xs leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-primary)" }}>
                {msg.content}
              </div>
              {msg.tool && (
                <div className="mt-1.5 pt-1.5 border-t border-slate-700/30">
                  <span className="text-[9px] text-emerald-500/60">🔧 {msg.tool}</span>
                </div>
              )}
              {msg.timestamp && (
                <div className="text-[9px] text-slate-600 mt-1">{msg.timestamp}</div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <Bot size={11} className="text-emerald-400" />
            </div>
            <div className="bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <Loader2 size={10} className="animate-spin text-emerald-400" />
                <span className="text-xs text-slate-400">正在处理...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="px-3 py-2 flex flex-wrap gap-1.5 border-t" style={{ borderColor: "var(--border-color)" }}>
        {QUICK_ACTIONS.map((a) => (
          <button
            key={a}
            onClick={() => handleSend(a.replace(/^[^\s]+\s/, ""))}
            className="px-2.5 py-1 text-[10px] text-slate-500 rounded-md hover:text-slate-300 hover:bg-white/5 transition-colors"
            style={{ border: "1px solid var(--border-color)" }}
          >
            {a}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 border-t" style={{ borderColor: "var(--border-color)" }}>
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="跟我说你想做什么... 如「回测茅台」「看看持仓」"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs
                       placeholder:text-slate-600 focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || loading}
            className="w-9 h-9 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40
                       disabled:cursor-not-allowed flex items-center justify-center transition-colors flex-shrink-0"
          >
            <Send size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}
