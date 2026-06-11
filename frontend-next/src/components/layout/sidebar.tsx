"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Bot,
  FlaskConical,
  BarChart3,
  Factory,
  Shield,
  PieChart,
  Gamepad2,
  Radio,
  TrendingUp,
  Trophy,
} from "lucide-react";

const menus = [
  { icon: Home, label: "工作台", href: "/" },
  { icon: Bot, label: "AI研究", href: "/ai-lab" },
  { icon: FlaskConical, label: "策略实验", href: "/strategy-lab" },
  { icon: BarChart3, label: "回测中心", href: "/backtest" },
  { icon: Gamepad2, label: "模拟交易", href: "/paper-trading" },
  { icon: Factory, label: "Alpha工厂", href: "/alpha-factory" },
  { icon: Trophy, label: "策略对比", href: "/compare" },
  { icon: Radio, label: "信号追踪", href: "/signals" },
  { icon: TrendingUp, label: "行情中心", href: "/marketplace" },
  { icon: PieChart, label: "投资组合", href: "/portfolio" },
  { icon: Shield, label: "风险中心", href: "/risk" },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside
      className="w-44 border-r flex flex-col flex-shrink-0"
      style={{ borderColor: "var(--border-color)", backgroundColor: "var(--bg-sidebar)" }}
    >
      {/* 品牌区 */}
      <div
        className="h-16 flex items-center gap-2.5 px-4 border-b"
        style={{ borderColor: "var(--border-color)" }}
      >
        <div
          className="rounded-lg bg-[#07111F] border p-1 flex items-center justify-center flex-shrink-0"
          style={{
            borderColor: "rgba(0,230,118,0.25)",
            boxShadow: "0 0 16px rgba(0,230,118,0.08)",
          }}
        >
          <img src="/slogo.svg" alt="青鳄量化" className="w-7 h-7" />
        </div>
        <div className="flex flex-col leading-tight">
          <span
            className="text-sm font-bold tracking-wider whitespace-nowrap"
            style={{ color: "#E5E7EB" }}
          >
            青鳄量化
          </span>
          <span
            className="text-[9px] font-bold tracking-[2px]"
            style={{ color: "#64748B", fontFamily: "'JetBrains Mono', Consolas, monospace" }}
          >
            QINGE QUANT
          </span>
        </div>
      </div>

      <nav className="flex-1 py-3">
        {menus.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.label}
              href={item.href}
              title={item.label}
              className={`
                h-12 flex items-center gap-3 px-5 mx-2 rounded-lg
                transition-colors duration-150 relative
                ${active
                  ? "text-emerald-400"
                  : "text-slate-500 hover:text-slate-300"
                }
              `}
            >
              {active && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-emerald-400 rounded-r-full" />
              )}
              <item.icon size={18} />
              <span className="text-xs font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
