"use client";

import { Store, TrendingUp, Star, Download } from "lucide-react";

export default function MarketplaceHeader({ totalCount, filteredCount }: { totalCount: number; filteredCount: number }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
          <Store size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold">Strategy Marketplace</h1>
          <p className="text-xs text-slate-500">Browse, clone, and deploy strategies</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-1.5">
            <Star size={12} className="text-amber-400" />
            <span className="text-slate-400">{totalCount} strategies</span>
          </div>
          <div className="flex items-center gap-1.5">
            <TrendingUp size={12} className="text-emerald-400" />
            <span className="text-slate-400">{filteredCount} shown</span>
          </div>
        </div>
      </div>
    </div>
  );
}
