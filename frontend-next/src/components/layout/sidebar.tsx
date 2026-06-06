"use client";

import Link from "next/link";
import {
  Home,
  Bot,
  Zap,
  FlaskConical,
  BarChart3,
  Factory,
  Store,
  Shield,
  PieChart,
  Database,
  CandlestickChart,
} from "lucide-react";
import { useState } from "react";

const menus = [
  { icon: Home, label: "工作台", href: "/" },
  { icon: Bot, label: "AI研究", href: "/ai-lab" },
  { icon: Zap, label: "Workflow", href: "/workflow" },
  { icon: FlaskConical, label: "策略实验室", href: "/strategy-lab" },
  { icon: BarChart3, label: "回测中心", href: "#" },
  { icon: Factory, label: "Alpha Factory", href: "/alpha-factory" },
  { icon: Store, label: "Marketplace", href: "/marketplace" },
  { icon: PieChart, label: "投资组合", href: "/portfolio" },
  { icon: Shield, label: "风险中心", href: "/risk" },
  { icon: CandlestickChart, label: "交易执行", href: "#" },
  { icon: Database, label: "数据中心", href: "#" },
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
          >
            <Link
              href={item.href}
              className={`
                h-16 flex flex-col items-center justify-center
                transition-colors duration-150
                ${active === idx
                  ? "bg-slate-800/60 text-blue-400"
                  : "text-slate-500 hover:bg-slate-900 hover:text-slate-300"
                }
              `}
            >
              <item.icon size={18} />
              <span className="text-[10px] mt-1.5 leading-none">{item.label}</span>
            </Link>
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
