"use client";

import { usePathname } from "next/navigation";

const pageTitles: Record<string, string> = {
  "/": "工作台",
  "/ai-lab": "AI 研究",
  "/strategy-lab": "策略实验室",
  "/alpha-factory": "Alpha 工厂",
  "/portfolio": "投资组合",
  "/risk": "风险中心",
  "/backtest": "回测中心",
  "/paper-trading": "模拟交易",
};

export default function Header() {
  const pathname = usePathname();
  const title = pageTitles[pathname] ?? "青鳄量化 Pro";

  return (
    <header className="h-16 border-b flex items-center justify-between px-5 flex-shrink-0"
      style={{ borderColor: "var(--border-color)", backgroundColor: "var(--bg-sidebar)" }}>
      <div className="flex items-center gap-2">
        <h1 className="text-sm font-semibold tracking-tight" style={{ color: "var(--text-primary)" }}>
          {title}
        </h1>
        <span className="text-[10px] px-1.5 py-0.5 rounded-sm"
          style={{ backgroundColor: "rgba(34,197,94,0.1)", color: "var(--accent)" }}>
          A股
        </span>
      </div>
    </header>
  );
}
