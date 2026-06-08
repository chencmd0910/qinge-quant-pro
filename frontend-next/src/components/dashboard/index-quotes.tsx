"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface IndexItem {
  name: string;
  price: string;
  change: number;
  status: "up" | "down" | "flat";
}

const FALLBACK: IndexItem[] = [
  { name: "上证指数", price: "3157.28", change: 0.42, status: "up" },
  { name: "深证成指", price: "10623.47", change: -0.15, status: "down" },
  { name: "沪深300", price: "3865.12", change: 0.38, status: "up" },
  { name: "中证500", price: "5876.34", change: -0.21, status: "down" },
  { name: "中证1000", price: "6123.89", change: -0.45, status: "down" },
  { name: "创业板指", price: "2156.78", change: 0.55, status: "up" },
];

export default function IndexQuotes() {
  const [indices, setIndices] = useState<IndexItem[]>(FALLBACK);

  useEffect(() => {
    // TODO: 接入真实行情API /api/market/overview
    fetch("http://localhost:8000/api/market/overview")
      .then((r) => r.json())
      .then((data) => {
        if (data?.indices) setIndices(data.indices);
      })
      .catch(() => {
        // fallback
      });
  }, []);

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp size={13} className="text-sky-400" />
        <span className="text-[11px] font-semibold">指数行情</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {indices.map((idx) => (
          <div
            key={idx.name}
            className="flex items-center justify-between p-2 rounded-lg"
            style={{ backgroundColor: "rgba(255,255,255,0.02)" }}
          >
            <span className="text-[10px] text-slate-400 w-14">{idx.name}</span>
            <span className="text-[11px] font-mono font-semibold">{idx.price}</span>
            <span className={`text-[10px] font-mono flex items-center gap-0.5 ${
              idx.status === "up" ? "text-red-400" : "text-green-400"
            }`}>
              {idx.status === "up" ? <TrendingUp size={8} /> : <TrendingDown size={8} />}
              {idx.change >= 0 ? "+" : ""}{idx.change.toFixed(2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
