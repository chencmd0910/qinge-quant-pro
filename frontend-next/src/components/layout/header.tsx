"use client";

import { Bell, Search, Settings } from "lucide-react";

export default function Header() {
  return (
    <header className="h-16 border-b border-slate-800 flex items-center justify-between px-6 bg-slate-950/80 backdrop-blur-sm">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold tracking-tight">青鳄量化 Pro</h1>
        <span className="text-xs text-slate-500 bg-slate-800/60 px-2 py-0.5 rounded">
          Mission Control
        </span>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5">
          <Search size={14} className="text-slate-500" />
          <span className="text-xs text-slate-500">搜索策略、标的...</span>
        </div>

        <button className="relative p-2 rounded-lg hover:bg-slate-800 transition-colors">
          <Bell size={16} className="text-slate-400" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
        </button>

        <button className="p-2 rounded-lg hover:bg-slate-800 transition-colors">
          <Settings size={16} className="text-slate-400" />
        </button>

        <div className="ml-2 flex items-center gap-2">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <span className="text-xs text-emerald-400">系统运行中</span>
        </div>
      </div>
    </header>
  );
}
