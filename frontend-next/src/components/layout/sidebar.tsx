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
} from "lucide-react";

const menus = [
  { icon: Home, label: "工作台", href: "/" },
  { icon: Bot, label: "AI研究", href: "/ai-lab" },
  { icon: FlaskConical, label: "策略实验", href: "/strategy-lab" },
  { icon: BarChart3, label: "回测中心", href: "/backtest" },
  { icon: Gamepad2, label: "模拟交易", href: "/paper-trading" },
  { icon: Factory, label: "Alpha工厂", href: "/alpha-factory" },
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
      {/* 品牌区: 盾标 + 青鳄量化 */}
      <div
        className="flex flex-col items-center justify-center gap-2 py-5 border-b"
        style={{ borderColor: "var(--border-color)" }}
      >
        <div
          className="rounded-xl bg-[#07111F] border p-2 flex items-center justify-center"
          style={{
            borderColor: "rgba(0,230,118,0.25)",
            boxShadow: "0 0 24px rgba(0,230,118,0.08)",
          }}
        >
          <img src="/slogo.svg" alt="青鳄量化" className="w-11 h-11" />
        </div>
        <div className="text-center">
          <div
            className="text-sm font-bold tracking-wider"
            style={{ color: "#E5E7EB" }}
          >
            青鳄量化
          </div>
          <div
            className="text-[9px] font-bold tracking-[2px] mt-0.5"
            style={{ color: "#64748B", fontFamily: "'JetBrains Mono', Consolas, monospace" }}
          >
            QINGE QUANT
          </div>
        </div>
      </div>

      {/* 导航菜单 */}
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
