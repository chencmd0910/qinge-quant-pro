"use client";

import { useState } from "react";
import {
  FolderOpen,
  FileCode2,
  Play,
  ChevronRight,
  ChevronDown,
  FlaskConical,
  BarChart3,
  Cpu,
  TrendingUp,
  Zap,
} from "lucide-react";

interface StrategyItem {
  id: string;
  name: string;
  type: "folder" | "strategy";
  status?: string;
  children?: StrategyItem[];
  code?: string;
}

const strategyTree: StrategyItem[] = [
  {
    id: "etf-rotation",
    name: "ETF Rotation",
    type: "folder",
    children: [
      {
        id: "etf-v6f",
        name: "V6F 量价_6F",
        type: "strategy",
        status: "ACTIVE",
        code: `class ETFRotationV6F(IndicatorStrategy):
    """ETF轮动策略 V6F - 量价因子"""

    symbols = ["510300.SH", "510500.SH", "159915.SZ", "515080.SH"]
    lookback = 60
    rebalance_day = "friday"

    def indicators(self, bars):
        self.volume_ratio = self.calc_volume_ratio(bars, 5)
        self.money_flow = self.calc_money_flow(bars, 5)
        self.mom_5d = self.calc_returns(bars, 5)
        self.mom_10d = self.calc_returns(bars, 10)
        self.volatility = self.calc_volatility(bars, 20)
        self.daily_sharpe = self.calc_sharpe(bars, 20)

    def generate_signal(self, bars):
        composite = (
            0.22 * self.volume_ratio +
            0.17 * self.money_flow +
            0.10 * self.mom_5d +
            0.10 * self.mom_10d +
            0.05 * self.volatility +
            0.05 * self.daily_sharpe
        )
        return self.rank_and_select(composite, top_n=1)`,
      },
      {
        id: "etf-basic",
        name: "基础版 ETF Rotation",
        type: "strategy",
        status: "VALIDATED",
        code: `class ETFRotationBasic(IndicatorStrategy):
    """ETF轮动策略 - 基础版"""

    symbols = ["510300.SH", "510500.SH", "159915.SZ"]
    lookback = 20

    def generate_signal(self, bars):
        returns = self.calc_returns(bars, self.lookback)
        best = max(returns, key=returns.get)
        return Signal(best, "BUY", strength=1.0)`,
      },
    ],
  },
  {
    id: "multi-factor",
    name: "Multi-Factor",
    type: "folder",
    children: [
      {
        id: "mf-v25",
        name: "V25 多因子",
        type: "strategy",
        status: "ACTIVE",
        code: `class MultiFactorV25(ScriptStrategy):
    """多因子策略 V25 - 北向+融资+行业"""

    factors = {
        "northbound_net_buy": 0.10,
        "northbound_holding_chg": 0.10,
        "margin_balance_chg": 0.08,
        "margin_buy_ratio": 0.07,
        "industry_revenue_growth": 0.08,
        "industry_profit_growth": 0.07,
        "industry_pmi": 0.05,
        "mom_5d": 0.06,
        "mom_10d": 0.05,
        "volume_ratio": 0.08,
        "money_flow": 0.07,
        "volatility_20d": 0.05,
        "daily_sharpe": 0.05,
        "pe_ttm": 0.03,
        "pb_ttm": 0.02,
    }

    def generate(self):
        scores = {}
        for symbol in self.universe:
            score = sum(
                weight * self.get_factor(symbol, factor)
                for factor, weight in self.factors.items()
            )
            scores[symbol] = score
        return self.rank(scores, top_n=20)`,
      },
    ],
  },
  {
    id: "industry",
    name: "Industry Rotation",
    type: "folder",
    children: [
      {
        id: "ind-v1",
        name: "行业轮动 V1",
        type: "strategy",
        status: "RESEARCH",
        code: `class IndustryRotationV1(ScriptStrategy):
    """行业轮动策略 V1"""

    def generate(self):
        sectors = self.get_sector_performance(lookback=20)
        top_sectors = sorted(sectors, key=sectors.get, reverse=True)[:3]
        return self.allocate_equal(top_sectors)`,
      },
    ],
  },
  {
    id: "templates",
    name: "Templates",
    type: "folder",
    children: [
      {
        id: "tpl-indicator",
        name: "Indicator Strategy Template",
        type: "strategy",
        code: `class MyIndicatorStrategy(IndicatorStrategy):
    """自定义指标策略模板"""

    def setup(self):
        # 初始化参数
        self.short_window = 5
        self.long_window = 20

    def indicators(self, bars):
        # 计算指标
        self.ma_short = self.sma(bars, self.short_window)
        self.ma_long = self.sma(bars, self.long_window)

    def buy_signal(self, bars) -> bool:
        # 买入条件
        return self.ma_short > self.ma_long

    def sell_signal(self, bars) -> bool:
        # 卖出条件
        return self.ma_short < self.ma_long`,
      },
      {
        id: "tpl-script",
        name: "Script Strategy Template",
        type: "strategy",
        code: `class MyScriptStrategy(ScriptStrategy):
    """自定义脚本策略模板"""

    def setup(self):
        self.lookback = 20
        self.top_n = 10

    def generate(self):
        # 完全自定义逻辑
        scores = {}
        for symbol in self.universe:
            score = self.calculate_score(symbol)
            scores[symbol] = score

        # 选取得分最高的标的
        selected = sorted(scores, key=scores.get, reverse=True)[:self.top_n]
        return self.allocate_equal(selected)

    def calculate_score(self, symbol):
        # 自定义评分逻辑
        momentum = self.get_returns(symbol, self.lookback)
        volatility = self.get_volatility(symbol, self.lookback)
        return momentum / volatility if volatility > 0 else 0`,
      },
    ],
  },
];

const statusColors: Record<string, string> = {
  ACTIVE: "bg-emerald-500/10 text-emerald-400",
  VALIDATED: "bg-blue-500/10 text-blue-400",
  WATCHLIST: "bg-amber-500/10 text-amber-400",
  RESEARCH: "bg-slate-500/10 text-slate-400",
  RETIRED: "bg-red-500/10 text-red-400",
};

function TreeItem({
  item,
  depth = 0,
  onSelect,
  selectedId,
}: {
  item: StrategyItem;
  depth?: number;
  onSelect: (item: StrategyItem) => void;
  selectedId: string | null;
}) {
  const [expanded, setExpanded] = useState(depth === 0);

  if (item.type === "folder") {
    return (
      <div>
        <div
          className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-slate-800/60 cursor-pointer"
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <ChevronDown size={12} className="text-slate-500" />
          ) : (
            <ChevronRight size={12} className="text-slate-500" />
          )}
          <FolderOpen size={14} className="text-amber-400" />
          <span className="text-xs font-medium">{item.name}</span>
        </div>
        {expanded && item.children && (
          <div>
            {item.children.map((child) => (
              <TreeItem
                key={child.id}
                item={child}
                depth={depth + 1}
                onSelect={onSelect}
                selectedId={selectedId}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors ${
        selectedId === item.id ? "bg-blue-500/10 border border-blue-500/30" : "hover:bg-slate-800/60"
      }`}
      style={{ paddingLeft: `${depth * 12 + 24}px` }}
      onClick={() => onSelect(item)}
    >
      <FileCode2 size={14} className="text-blue-400" />
      <span className="text-xs truncate flex-1">{item.name}</span>
      {item.status && (
        <span className={`text-[9px] px-1.5 py-0.5 rounded ${statusColors[item.status] || ""}`}>
          {item.status}
        </span>
      )}
    </div>
  );
}

export default function StrategyTree() {
  const [selected, setSelected] = useState<StrategyItem | null>(null);

  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <FlaskConical size={14} className="text-violet-400" />
          <span className="text-xs font-semibold">Strategy Tree</span>
        </div>
        <button className="p-1 rounded hover:bg-slate-800 transition-colors">
          <Play size={12} className="text-emerald-400" />
        </button>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-auto p-2">
        {strategyTree.map((item) => (
          <TreeItem
            key={item.id}
            item={item}
            onSelect={setSelected}
            selectedId={selected?.id || null}
          />
        ))}
      </div>

      {/* Stats */}
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="text-xs font-bold font-mono text-emerald-400">2</div>
            <div className="text-[8px] text-slate-500">ACTIVE</div>
          </div>
          <div>
            <div className="text-xs font-bold font-mono text-blue-400">1</div>
            <div className="text-[8px] text-slate-500">VALIDATED</div>
          </div>
          <div>
            <div className="text-xs font-bold font-mono text-slate-400">1</div>
            <div className="text-[8px] text-slate-500">RESEARCH</div>
          </div>
        </div>
      </div>
    </div>
  );
}
