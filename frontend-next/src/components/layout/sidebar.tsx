"use client";

import {
  Home,
  Bot,
  FlaskConical,
  BarChart3,
  Shield,
  PieChart,
  Database,
  CandlestickChart,
} from "lucide-react";
import { useState } from "react";

const menus = [
  { icon: Home, label: "工作台" },
  { icon: Bot, label: "AI研究" },
  { icon: FlaskConical, label: "策略实验室" },
  { icon: BarChart3, label: "回测中心" },
  { icon: PieChart, label: "投资组合" },
  { icon: Shield, label: "风险中心" },
  { icon: CandlestickChart, label: "交易执行" },
  { icon: Database, label: "数据中心" },
];

export default function Sidebar() {
  const [active, setActive] = useState(0);

  return (
    <aside className="w-20 border-r border-slate-800 flex flex-col">
      <div className="h-16 flex items-center justify-center border-b border-slate-800">
        <div className="text-2xl">🐊</div>
      </div>

      <nav className="flex-1">
        {menus.map((item, idx) => (
          <div
            key={item.label}
            onClick={() => setActive(idx)}
            className={`
              h-16 flex flex-col items-center justify-center cursor-pointer
              transition-colors duration-150
              ${active === idx
                ? "bg-slate-800/60 text-blue-400"
                : "text-slate-500 hover:bg-slate-900 hover:text-slate-300"
              }
            `}
          >
            <item.icon size={18} />
            <span className="text-[10px] mt-1.5 leading-none">{item.label}</span>
          </div>
        ))}
      </nav>

      <div className="p-3 border-t border-slate-800">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-xs font-bold mx-auto">
          C
        </div>
      </div>
    </aside>
  );
}
