"use client";

import { useEffect, useState } from "react";
import { TrendingUp, BarChart3, PieChart, Droplets, CheckCircle2, AlertTriangle } from "lucide-react";
import api from "@/lib/axios";

interface CategoryItem {
  label: string;
  value: string;
  status: string;
}

interface Category {
  name: string;
  icon: string;
  score: number;
  status: string;
  items: CategoryItem[];
}

const iconMap: Record<string, any> = {
  trending: TrendingUp,
  chart: BarChart3,
  pie: PieChart,
  droplets: Droplets,
};

const statusColors: Record<string, string> = {
  "低": "text-emerald-400 bg-emerald-500/10",
  "中": "text-amber-400 bg-amber-500/10",
  "高": "text-red-400 bg-red-500/10",
};

export default function RiskCategories() {
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    api.get("/api/risk/categories")
      .then(({ data }) => setCategories(data.categories || []))
      .catch(() => {});
  }, []);

  if (!categories.length) return null;

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex-1">
      <div className="text-xs font-semibold mb-3">风险分类</div>

      <div className="space-y-3">
        {categories.map((cat) => {
          const Icon = iconMap[cat.icon] || PieChart;
          return (
            <div key={cat.name} className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/20">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Icon size={12} className="text-blue-400" />
                  <span className="text-xs font-medium">{cat.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold">{cat.score}</span>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded ${statusColors[cat.status] || statusColors["中"]}`}>
                    {cat.status}
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                {cat.items.map((item) => (
                  <div key={item.label} className="flex items-center justify-between text-[10px]">
                    <span className="text-slate-500">{item.label}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-slate-300">{item.value}</span>
                      {item.status === "ok" ? (
                        <CheckCircle2 size={10} className="text-emerald-500" />
                      ) : (
                        <AlertTriangle size={10} className="text-amber-500" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
