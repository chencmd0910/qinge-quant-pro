"use client";

import { Trophy, TrendingUp, TrendingDown, Award } from "lucide-react";

const rankings = [
  { rank: 1, name: "V6F 量价_6F", annual: 19.57, dd: -5.0, sharpe: 2.5, alpha: 16.9, status: "ACTIVE" },
  { rank: 2, name: "8F_weekly", annual: 16.09, dd: -10.11, sharpe: 2.018, alpha: 13.8, status: "ACTIVE" },
  { rank: 3, name: "8F_weekly", annual: 14.05, dd: -6.8, sharpe: 2.5, alpha: 12.3, status: "ACTIVE" },
  { rank: 4, name: "8F_biweekly", annual: 10.83, dd: -5.0, sharpe: 2.5, alpha: 8.5, status: "ACTIVE" },
  { rank: 5, name: "8F_weekly", annual: 9.36, dd: -5.0, sharpe: 2.034, alpha: 8.5, status: "ACTIVE" },
  { rank: 6, name: "F5F 基本面", annual: 15.04, dd: -13.46, sharpe: 1.594, alpha: 12.6, status: "WATCH" },
  { rank: 7, name: "4F_biweekly", annual: 11.73, dd: -9.73, sharpe: 1.704, alpha: 11.0, status: "RETIRED" },
  { rank: 8, name: "M5F 动量", annual: 11.06, dd: -10.09, sharpe: 1.612, alpha: 10.1, status: "ACTIVE" },
  { rank: 9, name: "5F_biweekly", annual: 9.16, dd: -6.19, sharpe: 1.779, alpha: 6.2, status: "ACTIVE" },
  { rank: 10, name: "8F_monthly", annual: 13.53, dd: -13.53, sharpe: 1.437, alpha: 11.3, status: "ACTIVE" },
];

const statusStyle: Record<string, string> = {
  ACTIVE: "bg-emerald-500/10 text-emerald-400",
  WATCH: "bg-amber-500/10 text-amber-400",
  RETIRED: "bg-red-500/10 text-red-400",
};

export default function TournamentTable() {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Trophy size={14} className="text-amber-400" />
        <h3 className="text-sm font-semibold">Strategy Tournament</h3>
        <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded ml-auto">
          Top 10
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-[10px] text-slate-500 uppercase tracking-wider">
              <th className="text-left pb-3 pr-3 font-medium">#</th>
              <th className="text-left pb-3 pr-3 font-medium">Strategy</th>
              <th className="text-right pb-3 pr-3 font-medium">Annual</th>
              <th className="text-right pb-3 pr-3 font-medium">MaxDD</th>
              <th className="text-right pb-3 pr-3 font-medium">Sharpe</th>
              <th className="text-right pb-3 pr-3 font-medium">Alpha</th>
              <th className="text-center pb-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((r) => (
              <tr
                key={r.rank}
                className="border-t border-slate-800/50 hover:bg-slate-800/30 transition-colors"
              >
                <td className="py-2.5 pr-3">
                  <div className={`w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold ${
                    r.rank <= 3 ? "bg-amber-500/20 text-amber-400" : "bg-slate-800 text-slate-500"
                  }`}>
                    {r.rank}
                  </div>
                </td>
                <td className="py-2.5 pr-3">
                  <span className="text-xs font-medium">{r.name}</span>
                </td>
                <td className="py-2.5 pr-3 text-right">
                  <span className={`text-xs font-mono ${r.annual > 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {r.annual > 0 ? "+" : ""}{r.annual}%
                  </span>
                </td>
                <td className="py-2.5 pr-3 text-right">
                  <span className="text-xs font-mono text-red-400">{r.dd}%</span>
                </td>
                <td className="py-2.5 pr-3 text-right">
                  <span className="text-xs font-mono">{r.sharpe.toFixed(3)}</span>
                </td>
                <td className="py-2.5 pr-3 text-right">
                  <span className="text-xs font-mono text-emerald-400">+{r.alpha}%</span>
                </td>
                <td className="py-2.5 text-center">
                  <span className={`text-[9px] px-2 py-0.5 rounded font-medium ${statusStyle[r.status]}`}>
                    {r.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
