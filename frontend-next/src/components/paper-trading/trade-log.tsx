"use client";

import { ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";

const trades = [
  { time: "14:32", action: "BUY", symbol: "159915.SZ", qty: 1000, price: 2.230, amount: 2230 },
  { time: "13:15", action: "SELL", symbol: "515080.SH", qty: 2000, price: 1.018, amount: 2036 },
  { time: "11:20", action: "BUY", symbol: "600519.SH", qty: 100, price: 1680, amount: 168000 },
  { time: "10:45", action: "SELL", symbol: "510500.SH", qty: 1000, price: 6.280, amount: 6280 },
  { time: "10:05", action: "BUY", symbol: "510300.SH", qty: 500, price: 3.820, amount: 1910 },
  { time: "09:35", action: "BUY", symbol: "159915.SZ", qty: 2000, price: 2.185, amount: 4370 },
  { time: "09:30", action: "SELL", symbol: "515080.SH", qty: 3000, price: 1.025, amount: 3075 },
];

export default function TradeLog() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <span className="text-xs font-semibold">Trade Log</span>
        <span className="text-[10px] text-slate-500">{trades.length} trades today</span>
      </div>

      <div className="flex-1 overflow-auto max-h-[180px]">
        <table className="w-full">
          <thead>
            <tr className="text-[10px] text-slate-500 uppercase tracking-wider">
              <th className="text-left px-4 py-2 font-medium">Time</th>
              <th className="text-left px-3 py-2 font-medium">Action</th>
              <th className="text-left px-3 py-2 font-medium">Symbol</th>
              <th className="text-right px-3 py-2 font-medium">Qty</th>
              <th className="text-right px-3 py-2 font-medium">Price</th>
              <th className="text-right px-4 py-2 font-medium">Amount</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t, idx) => (
              <tr key={idx} className="border-t border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-2">
                  <div className="flex items-center gap-1 text-[11px] text-slate-400">
                    <Clock size={9} />
                    {t.time}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <div className={`flex items-center gap-1 text-[11px] font-medium ${
                    t.action === "BUY" ? "text-emerald-400" : "text-red-400"
                  }`}>
                    {t.action === "BUY" ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                    {t.action}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <span className="text-[11px] font-mono">{t.symbol}</span>
                </td>
                <td className="px-3 py-2 text-right">
                  <span className="text-[11px] font-mono">{t.qty.toLocaleString()}</span>
                </td>
                <td className="px-3 py-2 text-right">
                  <span className="text-[11px] font-mono">{t.price.toFixed(3)}</span>
                </td>
                <td className="px-4 py-2 text-right">
                  <span className="text-[11px] font-mono">¥{t.amount.toLocaleString()}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
