"use client";

import { useState } from "react";
import MarketplaceHeader from "./marketplace-header";
import MarketplaceFilters from "./marketplace-filters";
import StrategyCard from "./strategy-card";
import StrategyDetail from "./strategy-detail";

export interface MarketplaceStrategy {
  id: string;
  name: string;
  category: string;
  version: string;
  rating: number;
  sharpe: number;
  alpha: number;
  maxDD: number;
  annual: number;
  winRate: number;
  trades: number;
  liveDays: number;
  factors: string[];
  description: string;
  author: string;
  clones: number;
  status: "ACTIVE" | "VALIDATED" | "RESEARCH";
}

const allStrategies: MarketplaceStrategy[] = [
  {
    id: "etf-v6f",
    name: "ETF Rotation V6F",
    category: "ETF Rotation",
    version: "V6F",
    rating: 5,
    sharpe: 2.5,
    alpha: 16.9,
    maxDD: -5.0,
    annual: 19.57,
    winRate: 100,
    trades: 108,
    liveDays: 127,
    factors: ["volume_ratio", "money_flow", "mom_5d", "mom_10d", "volatility_20d", "daily_sharpe"],
    description: "6因子量价ETF轮动策略，周度调仓，夏普比率2.5，Alpha+16.9%",
    author: "Qinge AI",
    clones: 24,
    status: "ACTIVE",
  },
  {
    id: "mf-v25",
    name: "Multi-Factor V25",
    category: "Multi-Factor",
    version: "V25",
    rating: 5,
    sharpe: 2.1,
    alpha: 12.5,
    maxDD: -18.5,
    annual: 15.04,
    winRate: 58,
    trades: 240,
    liveDays: 89,
    factors: ["northbound_net_buy", "margin_balance_chg", "industry_revenue_growth", "volume_ratio", "money_flow"],
    description: "15因子多因子策略，北向+融资+行业+量价，月度调仓",
    author: "Qinge AI",
    clones: 18,
    status: "ACTIVE",
  },
  {
    id: "nb-alpha",
    name: "Northbound Alpha NF4F",
    category: "Northbound",
    version: "NF4F",
    rating: 4,
    sharpe: 1.704,
    alpha: 11.0,
    maxDD: -9.73,
    annual: 11.73,
    winRate: 55,
    trades: 180,
    liveDays: 14,
    factors: ["northbound_net_buy", "northbound_holding_chg", "margin_balance_chg", "volume_ratio"],
    description: "北向资金因子策略，捕捉外资流入信号，双周调仓",
    author: "Qinge AI",
    clones: 12,
    status: "VALIDATED",
  },
  {
    id: "m5f-momentum",
    name: "Momentum M5F",
    category: "Momentum",
    version: "M5F",
    rating: 4,
    sharpe: 1.612,
    alpha: 10.1,
    maxDD: -10.09,
    annual: 11.06,
    winRate: 52,
    trades: 160,
    liveDays: 45,
    factors: ["mom_5d", "mom_10d", "consistency", "mom_20d", "volume_ratio"],
    description: "5因子动量策略，短期动量为主，周度调仓",
    author: "Qinge AI",
    clones: 9,
    status: "VALIDATED",
  },
  {
    id: "ff4f-fundflow",
    name: "Fund Flow FF4F",
    category: "Fund Flow",
    version: "FF4F",
    rating: 4,
    sharpe: 1.704,
    alpha: 11.0,
    maxDD: -9.73,
    annual: 11.73,
    winRate: 54,
    trades: 150,
    liveDays: 30,
    factors: ["money_flow", "northbound_net_buy", "margin_balance_chg", "volume_ratio"],
    description: "资金流因子策略，主力+北向+融资三维资金分析",
    author: "Qinge AI",
    clones: 7,
    status: "VALIDATED",
  },
  {
    id: "ind-v1",
    name: "Industry Rotation V1",
    category: "Industry",
    version: "V1",
    rating: 3,
    sharpe: 0.72,
    alpha: 6.2,
    maxDD: -22.0,
    annual: 8.7,
    winRate: 52,
    trades: 180,
    liveDays: 7,
    factors: ["industry_revenue_growth", "industry_profit_growth", "industry_pmi"],
    description: "行业轮动策略，基于行业景气度指标，月度调仓",
    author: "Qinge AI",
    clones: 4,
    status: "RESEARCH",
  },
  {
    id: "boll-v2",
    name: "Bollinger Breakout V2",
    category: "Technical",
    version: "V2",
    rating: 3,
    sharpe: 0.95,
    alpha: 5.8,
    maxDD: -15.0,
    annual: 7.5,
    winRate: 48,
    trades: 220,
    liveDays: 60,
    factors: ["boll_pos", "rsi_14", "macd_hist", "atr_14"],
    description: "布林带突破策略，结合RSI和MACD确认信号",
    author: "Community",
    clones: 6,
    status: "VALIDATED",
  },
  {
    id: "low-vol",
    name: "Low Volatility Factor",
    category: "Factor",
    version: "V1",
    rating: 3,
    sharpe: 1.1,
    alpha: 7.2,
    maxDD: -12.0,
    annual: 9.0,
    winRate: 56,
    trades: 120,
    liveDays: 20,
    factors: ["volatility_20d", "atr_14", "daily_sharpe", "pe_ttm"],
    description: "低波动因子策略，优选低波动高夏普标的",
    author: "Community",
    clones: 3,
    status: "VALIDATED",
  },
];

export default function MarketplaceLayout() {
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [minSharpe, setMinSharpe] = useState(0);
  const [maxDD, setMaxDD] = useState(100);
  const [selectedStrategy, setSelectedStrategy] = useState<MarketplaceStrategy | null>(null);

  const categories = ["All", "ETF Rotation", "Multi-Factor", "Northbound", "Momentum", "Fund Flow", "Industry", "Technical", "Factor"];

  const filtered = allStrategies.filter((s) => {
    if (selectedCategory !== "All" && s.category !== selectedCategory) return false;
    if (s.sharpe < minSharpe) return false;
    if (Math.abs(s.maxDD) > maxDD) return false;
    return true;
  });

  return (
    <div className="h-full flex flex-col gap-4">
      <MarketplaceHeader totalCount={allStrategies.length} filteredCount={filtered.length} />

      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        {/* Left: Filters */}
        <div className="col-span-2">
          <MarketplaceFilters
            categories={categories}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            minSharpe={minSharpe}
            onSharpeChange={setMinSharpe}
            maxDD={maxDD}
            onDDChange={setMaxDD}
          />
        </div>

        {/* Center: Strategy grid */}
        <div className="col-span-6 overflow-auto">
          <div className="grid grid-cols-2 gap-3">
            {filtered.map((s) => (
              <StrategyCard
                key={s.id}
                strategy={s}
                onClick={() => setSelectedStrategy(s)}
                isSelected={selectedStrategy?.id === s.id}
              />
            ))}
          </div>
        </div>

        {/* Right: Detail */}
        <div className="col-span-4">
          <StrategyDetail strategy={selectedStrategy} />
        </div>
      </div>
    </div>
  );
}
