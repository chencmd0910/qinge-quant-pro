"use client";

import { TrendingUp, TrendingDown } from "lucide-react";

const positions = [
  { symbol: "159915.SZ", name: "创业板ETF", qty: 5000, avgCost: 2.185, current: 2.230, pnl: 225, pnlPct: 2.06 },
  { symbol: "510300.SH", name: "沪深300ETF", qty: 3000, avgCost: 3.820, current: 3.855, pnl: 105, pnlPct: 0.92 },
  { symbol: "510500.SH", name: "中证500ETF", qty: 2000, avgCost: 6.150, current: 6.280, pnl: 260, pnlPct: 2.11 },
  { symbol: "515080.SH", name: "红利ETF", qty: 4000, avgCost: 1.025, current: 1.018, pnl: -28, pnlPct: -0.68 },
  { symbol: "600519.SH", name: "贵州茅台", qty: 100, avgCost: 1680, current: 1705, pnl: 2500, pnlPct: 1.49 },
];

export default function PositionsTable() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col flex-1">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <span className="text-xs font-semibold">Positions</span>
        <span className="text-[10px] text-slate-500">{positions.length} holdings</span>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead>
            <tr className="text-[10px] text-slate-500 uppercase tracking-wider">
              <th className="text-left px-4 py-2 font-medium">Symbol</th>
              <th className="text-right px-3 py-2 font-medium">Qty</th>
              <th className="text-right px-3 py-2 font-medium">Avg Cost</th>
              <th className="text-right px-3 py-2 font-medium">Current</th>
              <th className="text-right px-4 py-2 font-medium">P&L</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={p.symbol} className="border-t border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-2.5">
                  <div className="text-xs font-medium">{p.symbol}</div>
                  <div className="text-[10px] text-slate-500">{p.name}</div>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <span className="text-xs font-mono">{p.qty.toLocaleString()}</span>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <span className="text-xs font-mono">{p.avgCost.toFixed(3)}</span>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <span className="text-xs font-mono">{p.current.toFixed(3)}</span>
                </td>
                <td className="px-4 py-2.5 text-right">
                  <div className="flex items-center justify-end gap-1">
                    {p.pnl >= 0 ? (
                      <TrendingUp size={10} className="text-emerald-400" />
                    ) : (
                      <TrendingDown size={10} className="text-red-400" />
                    )}
                    <span className={`text-xs font-mono ${p.pnl >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {p.pnl >= 0 ? "+" : ""}{p.pnl}
                    </span>
                  </div>
                  <span className={`text-[9px] font-mono ${p.pnlPct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {p.pnlPct >= 0 ? "+" : ""}{p.pnlPct}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex justify-between text-[10px]">
          <span className="text-slate-500">Total Positions Value</span>
          <span className="font-mono font-semibold">¥1,124,500</span>
        </div>
      </div>
    </div>
  );
}
