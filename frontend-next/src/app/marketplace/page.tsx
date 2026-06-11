"use client";

import { useEffect, useState, useCallback } from "react";
import { TrendingUp, BarChart3, Flame, DollarSign } from "lucide-react";
import ReactECharts from "echarts-for-react";

interface SectorItem {
  name: string;
  change: number;
  inflow: number;
  heat?: number;
  leader?: string;
}

interface MarketOverview {
  date: string;
  up_count: number;
  down_count: number;
  flat_count: number;
  limit_up: number;
  limit_down: number;
  avg_change: number;
  zhaban_rate: number;
  total_amount: number;
  amount_change_pct: number;
  distribution?: { labels: string[]; data: number[] };
}

interface MarketIndex {
  date: string;
  sh: { value: number; change_pct: number };
  sz: { value: number; change_pct: number };
  cy: { value: number; change_pct: number };
}

export default function MarketplacePage() {
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [index, setIndex] = useState<MarketIndex | null>(null);
  const [sectors, setSectors] = useState<SectorItem[]>([]);
  const [heatmap, setHeatmap] = useState<SectorItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [ovRes, idxRes, secRes, hmRes] = await Promise.all([
        fetch("/api/market/overview").then(r => r.json()).catch(() => null),
        fetch("/api/market/index").then(r => r.json()).catch(() => null),
        fetch("/api/market/sectors").then(r => r.json()).catch(() => []),
        fetch("/api/market/heatmap").then(r => r.json()).catch(() => []),
      ]);
      if (ovRes && ovRes.date) setOverview(ovRes);
      if (idxRes && idxRes.date) setIndex(idxRes);
      if (Array.isArray(secRes)) setSectors(secRes.slice(0, 30));
      if (Array.isArray(hmRes)) setHeatmap(hmRes.slice(0, 30));
    } catch {}
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  const formatPct = (v: number) => `${v > 0 ? "+" : ""}${v?.toFixed(2)}%`;

  const sectorTreemapOpt = heatmap.length > 0 ? {
    tooltip: {
      formatter: (p: any) => `${p.name}<br/>涨跌: ${p.value > 0 ? "+" : ""}${p.value.toFixed(2)}%<br/>流入: ${p.data?.inflow?.toFixed(1) || "0"}亿`,
      backgroundColor: "#1e293b",
      textStyle: { color: "#e2e8f0", fontSize: 12 },
    },
    series: [{
      type: "treemap",
      data: heatmap.map(s => ({
        name: s.name,
        value: s.heat ?? Math.abs(s.change) * 2,
        inflow: s.inflow,
        change_display: s.change,
        itemStyle: {
          color: s.change > 0
            ? `rgba(34,197,94,${0.25 + Math.min(Math.abs(s.change)/12, 0.75)})`
            : `rgba(239,68,68,${0.25 + Math.min(Math.abs(s.change)/12, 0.75)})`,
        },
      })),
      label: { show: false },
      upperLabel: { show: true, height: 20, fontSize: 10, color: "#e2e8f0" },
      itemStyle: { borderColor: "#0B1220", borderWidth: 2 },
      roam: false,
      nodeClick: false,
    }],
  } : null;

  // Index bar
  const idxList = index ? [
    { name: "上证指数", price: index.sh.value, change_pct: index.sh.change_pct },
    { name: "深证成指", price: index.sz.value, change_pct: index.sz.change_pct },
    { name: "创业板指", price: index.cy.value, change_pct: index.cy.change_pct },
  ] : [];

  // Distribution chart
  const distOpt = overview?.distribution ? {
    tooltip: { backgroundColor: "#1e293b", textStyle: { color: "#e2e8f0", fontSize: 12 } },
    grid: { left: 10, right: 10, top: 10, bottom: 5 },
    xAxis: {
      type: "category",
      data: overview.distribution.labels,
      axisLabel: { color: "#94a3b8", fontSize: 9, rotate: 20 },
    },
    yAxis: { show: false },
    series: [{
      type: "bar",
      data: overview.distribution.data.map((v, i) => ({
        value: v,
        itemStyle: {
          color: i < 4 ? "rgba(34,197,94,0.6)" : "rgba(239,68,68,0.6)",
          borderRadius: [3, 3, 0, 0],
        },
      })),
      barWidth: "60%",
    }],
  } : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center">
          <TrendingUp size={16} />
        </div>
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            行情中心
          </h1>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            指数概览 · 行业板块 · 涨跌分布 {overview?.date ? `· ${overview.date}` : ""}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20" style={{ color: "var(--text-muted)" }}>
          <BarChart3 size={20} className="animate-pulse" />
        </div>
      ) : (
        <>
          {/* Index Bar */}
          {idxList.length > 0 && (
            <div className="flex gap-3">
              {idxList.map((idx) => (
                <div key={idx.name}
                  className="flex-1 rounded-xl p-4"
                  style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}
                >
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>{idx.name}</div>
                  <div className="text-xl font-bold font-mono mt-1" style={{ color: "var(--text-primary)" }}>
                    {idx.price.toFixed(0)}
                  </div>
                  <div className={`text-xs font-mono mt-1 ${idx.change_pct > 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {idx.change_pct > 0 ? "+" : ""}{idx.change_pct.toFixed(2)}%
                  </div>
                </div>
              ))}
              {overview && (
                <div className="flex-1 rounded-xl p-4"
                  style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}
                >
                  <div className="text-xs" style={{ color: "var(--text-muted)" }}>市场统计</div>
                  <div className="text-xl font-bold font-mono mt-1" style={{ color: "var(--text-primary)" }}>
                    {overview.up_count + overview.down_count + overview.flat_count}
                  </div>
                  <div className="flex gap-2 text-[10px] mt-1">
                    <span style={{ color: "#22c55e" }}>↑{overview.up_count}</span>
                    <span style={{ color: "#ef4444" }}>↓{overview.down_count}</span>
                    <span style={{ color: "var(--text-muted)" }}>→{overview.flat_count}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* KPI cards */}
          {overview && (
            <div className="grid grid-cols-6 gap-3">
              <div className="rounded-xl p-3 text-center" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>涨停</div>
                <div className="text-lg font-bold font-mono" style={{ color: "#ef4444" }}>{overview.limit_up}</div>
              </div>
              <div className="rounded-xl p-3 text-center" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>跌停</div>
                <div className="text-lg font-bold font-mono" style={{ color: "#22c55e" }}>{overview.limit_down}</div>
              </div>
              <div className="rounded-xl p-3 text-center" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>均涨跌</div>
                <div className="text-lg font-bold font-mono" style={{ color: overview.avg_change > 0 ? "#22c55e" : "#ef4444" }}>
                  {overview.avg_change > 0 ? "+" : ""}{overview.avg_change}%
                </div>
              </div>
              <div className="rounded-xl p-3 text-center" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>炸板率</div>
                <div className="text-lg font-bold font-mono" style={{ color: "var(--text-secondary)" }}>{overview.zhaban_rate}%</div>
              </div>
              <div className="rounded-xl p-3 text-center" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>成交额</div>
                <div className="text-lg font-bold font-mono" style={{ color: "var(--text-primary)" }}>{overview.total_amount}亿</div>
              </div>
              <div className="rounded-xl p-3 text-center" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="text-[10px]" style={{ color: "var(--text-muted)" }}>量比</div>
                <div className={`text-lg font-bold font-mono ${overview.amount_change_pct > 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {overview.amount_change_pct > 0 ? "+" : ""}{overview.amount_change_pct}%
                </div>
              </div>
            </div>
          )}

          {/* Distribution + Treemap */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {distOpt && (
              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 size={14} style={{ color: "var(--accent-blue)" }} />
                  <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>涨跌分布</span>
                </div>
                <ReactECharts option={distOpt} style={{ height: 200 }} />
              </div>
            )}
            {sectorTreemapOpt && (
              <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
                <div className="flex items-center gap-2 mb-3">
                  <Flame size={14} style={{ color: "#f59e0b" }} />
                  <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>行业板块热度</span>
                </div>
                <ReactECharts option={sectorTreemapOpt} style={{ height: 320 }} />
              </div>
            )}
          </div>

          {/* Sector list */}
          {sectors.length > 0 && (
            <div className="rounded-xl overflow-hidden" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
              <div className="p-4 pb-2 flex items-center gap-2">
                <DollarSign size={14} style={{ color: "var(--accent)" }} />
                <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>板块排行</span>
              </div>
              <div className="grid grid-cols-3 lg:grid-cols-5 gap-0.5 p-2">
                {sectors.map((s, i) => (
                  <div key={i} className="p-2 rounded hover:bg-white/[0.03] transition-colors">
                    <div className="text-[11px] truncate" style={{ color: "var(--text-primary)" }}>{s.name}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-xs font-mono font-bold ${s.change > 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {s.change > 0 ? "+" : ""}{s.change}%
                      </span>
                      <span className="text-[9px]" style={{ color: "var(--text-muted)" }}>
                        {s.inflow > 0 ? "+" : ""}{s.inflow}亿
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
