"use client";

import { Filter, Star } from "lucide-react";

interface FiltersProps {
  categories: string[];
  selectedCategory: string;
  onCategoryChange: (c: string) => void;
  minSharpe: number;
  onSharpeChange: (v: number) => void;
  maxDD: number;
  onDDChange: (v: number) => void;
}

export default function MarketplaceFilters({
  categories,
  selectedCategory,
  onCategoryChange,
  minSharpe,
  onSharpeChange,
  maxDD,
  onDDChange,
}: FiltersProps) {
  return (
    <div className="h-full bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
        <Filter size={14} className="text-blue-400" />
        <span className="text-xs font-semibold">Filters</span>
      </div>

      {/* Category */}
      <div className="mb-5">
        <div className="text-[10px] text-slate-500 mb-2 uppercase tracking-wider">Category</div>
        <div className="space-y-1">
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => onCategoryChange(c)}
              className={`w-full text-left px-3 py-1.5 rounded-md text-xs transition-colors ${
                selectedCategory === c
                  ? "bg-blue-500/10 text-blue-400 border border-blue-500/30"
                  : "text-slate-400 hover:bg-slate-800/60"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Sharpe filter */}
      <div className="mb-5">
        <div className="text-[10px] text-slate-500 mb-2 uppercase tracking-wider">
          Min Sharpe: {minSharpe.toFixed(1)}
        </div>
        <input
          type="range"
          min={0}
          max={3}
          step={0.1}
          value={minSharpe}
          onChange={(e) => onSharpeChange(parseFloat(e.target.value))}
          className="w-full h-1 bg-slate-700 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:appearance-none"
        />
        <div className="flex justify-between text-[9px] text-slate-600 mt-1">
          <span>0</span>
          <span>3.0</span>
        </div>
      </div>

      {/* MaxDD filter */}
      <div className="mb-5">
        <div className="text-[10px] text-slate-500 mb-2 uppercase tracking-wider">
          Max Drawdown: {maxDD}%
        </div>
        <input
          type="range"
          min={5}
          max={50}
          step={1}
          value={maxDD}
          onChange={(e) => onDDChange(parseInt(e.target.value))}
          className="w-full h-1 bg-slate-700 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-red-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:appearance-none"
        />
        <div className="flex justify-between text-[9px] text-slate-600 mt-1">
          <span>5%</span>
          <span>50%</span>
        </div>
      </div>

      {/* Quick filters */}
      <div>
        <div className="text-[10px] text-slate-500 mb-2 uppercase tracking-wider">Quick</div>
        <div className="space-y-1">
          <button
            onClick={() => { onSharpeChange(1.5); onDDChange(15); }}
            className="w-full text-left px-3 py-1.5 rounded-md text-xs text-slate-400 hover:bg-slate-800/60 transition-colors"
          >
            ★ High Quality (S&gt;1.5, DD&lt;15%)
          </button>
          <button
            onClick={() => { onSharpeChange(2.0); onDDChange(10); }}
            className="w-full text-left px-3 py-1.5 rounded-md text-xs text-slate-400 hover:bg-slate-800/60 transition-colors"
          >
            ★★ Elite (S&gt;2.0, DD&lt;10%)
          </button>
          <button
            onClick={() => { onSharpeChange(0); onDDChange(100); }}
            className="w-full text-left px-3 py-1.5 rounded-md text-xs text-slate-400 hover:bg-slate-800/60 transition-colors"
          >
            Show All
          </button>
        </div>
      </div>
    </div>
  );
}
