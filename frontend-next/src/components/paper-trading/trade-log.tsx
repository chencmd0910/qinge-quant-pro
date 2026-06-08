"use client";

import { useEffect, useState } from "react";
import { ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";
import api from "@/lib/axios";

interface Trade {
  time: string;
  action: string;
  symbol: string;
  qty: number;
  price: number;
  amount: number;
}

export default function TradeLog() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/paper-trading/trades", { params: { limit: 15 } })
      .then(({ data }) => {
        setTrades(data.trades || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col"><div className="flex-1 animate-pulse p-4 space-y-2">{Array(7).fill(0).map((_,i)=><div key={i} className="h-6 bg-slate-800/50 rounded"/>)}</div></div>;
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <span className="text-xs font-semibold">交易日志</span>
        <span className="text-[10px] text-slate-500">{trades.length} 笔</span>
      </div>
      <div className="flex-1 overflow-auto max-h-[180px]">
        <table className="w-full">
          <thead>
            <tr className="text-[10px] text-slate-500 uppercase tracking-wider">
              <th className="text-left px-4 py-2 font-medium">日期</th>
              <th className="text-left px-3 py-2 font-medium">操作</th>
              <th className="text-left px-3 py-2 font-medium">代码</th>
              <th className="text-right px-3 py-2 font-medium">数量</th>
              <th className="text-right px-3 py-2 font-medium">价格</th>
              <th className="text-right px-4 py-2 font-medium">金额</th>
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
                  <div className={`flex items-center gap-1 text-[11px] font-medium ${t.action === "BUY" || t.action === "买入" ? "text-emerald-400" : "text-red-400"}`}>
                    {t.action === "BUY" || t.action === "买入" ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                    {t.action}
                  </div>
                </td>
                <td className="px-3 py-2"><span className="text-[11px] font-mono">{t.symbol}</span></td>
                <td className="px-3 py-2 text-right"><span className="text-[11px] font-mono">{t.qty.toLocaleString()}</span></td>
                <td className="px-3 py-2 text-right"><span className="text-[11px] font-mono">{t.price.toFixed(3)}</span></td>
                <td className="px-4 py-2 text-right"><span className="text-[11px] font-mono">¥{t.amount.toLocaleString()}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
