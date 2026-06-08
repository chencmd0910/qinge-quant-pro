"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import api from "@/lib/axios";

interface Position {
  symbol: string;
  name: string;
  qty: number;
  avg_cost: number;
  current: number;
  pnl: number;
  pnl_pct: number;
}

export default function PositionsTable() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/paper-trading/positions")
      .then(({ data }) => {
        setPositions(data.positions || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col flex-1"><div className="flex-1 animate-pulse p-4 space-y-3">{Array(5).fill(0).map((_,i) => <div key={i} className="h-8 bg-slate-800/50 rounded"/>) }</div></div>;
  }

  const totalValue = positions.reduce((s, p) => s + p.current * p.qty, 0);

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col flex-1">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <span className="text-xs font-semibold">持仓明细</span>
        <span className="text-[10px] text-slate-500">{positions.length} 只</span>
      </div>
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead>
            <tr className="text-[10px] text-slate-500 uppercase tracking-wider">
              <th className="text-left px-4 py-2 font-medium">代码</th>
              <th className="text-right px-3 py-2 font-medium">数量</th>
              <th className="text-right px-3 py-2 font-medium">成本</th>
              <th className="text-right px-3 py-2 font-medium">现价</th>
              <th className="text-right px-4 py-2 font-medium">盈亏</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p) => (
              <tr key={p.symbol} className="border-t border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-2.5">
                  <div className="text-xs font-medium font-mono">{p.symbol}</div>
                  <div className="text-[10px] text-slate-500">{p.name}</div>
                </td>
                <td className="px-3 py-2.5 text-right text-xs font-mono">{p.qty.toLocaleString()}</td>
                <td className="px-3 py-2.5 text-right text-xs font-mono">{p.avg_cost.toFixed(3)}</td>
                <td className="px-3 py-2.5 text-right text-xs font-mono">{p.current.toFixed(3)}</td>
                <td className="px-4 py-2.5 text-right">
                  <div className="flex items-center justify-end gap-1">
                    {p.pnl >= 0 ? <TrendingUp size={10} className="text-emerald-400"/> : <TrendingDown size={10} className="text-red-400"/>}
                    <span className={`text-xs font-mono ${p.pnl>=0?"text-emerald-400":"text-red-400"}`}>{p.pnl>=0?"+":""}{p.pnl}</span>
                  </div>
                  <span className={`text-[9px] font-mono ${p.pnl_pct>=0?"text-emerald-400":"text-red-400"}`}>{p.pnl_pct>=0?"+":""}{p.pnl_pct}%</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-3 border-t border-slate-800">
        <div className="flex justify-between text-[10px]">
          <span className="text-slate-500">持仓总市值</span>
          <span className="font-mono font-semibold">¥{totalValue.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
