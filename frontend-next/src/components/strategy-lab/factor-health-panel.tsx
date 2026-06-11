"use client";

import { useEffect, useState } from "react";
import { Activity, ChevronDown, ChevronRight, AlertTriangle, CheckCircle2 } from "lucide-react";
import ReactECharts from "echarts-for-react";

interface FactorItem {
  name: string;
  weight: number;
  category: string;
  status: string;
  ic?: number;
  ic_ir?: number;
  turnover?: number;
  decay?: number;
}

interface FactorHealthData {
  factors: FactorItem[];
  categories: Record<string, number>;
  total_factors: number;
  total_weight: number;
}

export default function FactorHealthPanel() {
  const [data, setData] = useState<FactorHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    fetch("/api/v25/factor-health")
      .then(r => r.json())
      .then(d => { if (d.factors) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl p-3 animate-pulse" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
        <div className="h-4 w-32 rounded" style={{ background: "var(--border-color)" }} />
      </div>
    );
  }

  if (!data?.factors?.length) return null;

  const healthy = data.factors.filter(f => f.status === "HEALTHY").length;
  const warning = data.factors.filter(f => f.status === "WATCH").length;
  const dead = data.factors.filter(f => f.status === "DEAD").length;

  const radarOpt = {
    radar: {
      indicator: Object.entries(data.categories || {}).map(([name, w]) => ({
        name: name.replace("_", ""),
        max: 0.5,
      })),
      shape: "polygon",
      splitArea: { areaStyle: { color: ["rgba(34,197,94,0.02)", "rgba(34,197,94,0.03)"] } },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.2)" } },
    },
    series: [{
      type: "radar",
      data: [{
        value: Object.values(data.categories || {}),
        name: "因子权重",
        areaStyle: { color: "rgba(34,197,94,0.15)" },
        lineStyle: { color: "#22c55e", width: 1.5 },
        itemStyle: { color: "#22c55e" },
      }],
    }],
  };

  return (
    <div className="rounded-xl" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div
        className="flex items-center justify-between p-3 cursor-pointer select-none"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-2">
          <Activity size={14} style={{ color: "var(--accent)" }} />
          <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
            因子健康监控
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ color: "var(--text-muted)", backgroundColor: "rgba(255,255,255,0.04)" }}>
            {data.total_factors}因子
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-[10px]">
            <span style={{ color: "#22c55e" }}>● {healthy}健康</span>
            <span style={{ color: "#eab308" }}>● {warning}预警</span>
            <span style={{ color: "#ef4444" }}>● {dead}失效</span>
          </div>
          {open ? <ChevronDown size={14} style={{ color: "var(--text-muted)" }} /> : <ChevronRight size={14} style={{ color: "var(--text-muted)" }} />}
        </div>
      </div>

      {open && (
        <div className="px-3 pb-3 border-t" style={{ borderColor: "var(--border-color)" }}>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3 mt-3">
            {/* Radar chart */}
            <div className="p-2 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.02)" }}>
              <div className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>因子权重分布</div>
              <ReactECharts option={radarOpt} style={{ height: 220 }} />
            </div>

            {/* Factor list */}
            <div className="overflow-auto" style={{ maxHeight: 280 }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-color)" }}>
                    <th style={{ padding: "6px 8px", textAlign: "left", fontSize: 10, color: "var(--text-muted)", fontWeight: 600 }}>因子</th>
                    <th style={{ padding: "6px 8px", textAlign: "right", fontSize: 10, color: "var(--text-muted)", fontWeight: 600 }}>权重%</th>
                    <th style={{ padding: "6px 8px", textAlign: "right", fontSize: 10, color: "var(--text-muted)", fontWeight: 600 }}>IC</th>
                    <th style={{ padding: "6px 8px", textAlign: "right", fontSize: 10, color: "var(--text-muted)", fontWeight: 600 }}>IC_IR</th>
                    <th style={{ padding: "6px 8px", textAlign: "center", fontSize: 10, color: "var(--text-muted)", fontWeight: 600 }}>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {data.factors.map((f, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                      <td style={{ padding: "5px 8px", color: "var(--text-primary)", fontWeight: 500 }}>
                        {f.name}
                      </td>
                      <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: "monospace", color: "var(--text-secondary)" }}>
                        {(f.weight * 100).toFixed(1)}
                      </td>
                      <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: "monospace", color: f.ic && f.ic > 0 ? "#22c55e" : "#ef4444" }}>
                        {f.ic?.toFixed(3) || "--"}
                      </td>
                      <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: "monospace", color: f.ic_ir && f.ic_ir > 0 ? "#22c55e" : "var(--text-muted)" }}>
                        {f.ic_ir?.toFixed(2) || "--"}
                      </td>
                      <td style={{ padding: "5px 8px", textAlign: "center" }}>
                        {f.status === "HEALTHY" ? (
                          <CheckCircle2 size={12} color="#22c55e" />
                        ) : f.status === "WATCH" ? (
                          <AlertTriangle size={12} color="#eab308" />
                        ) : (
                          <AlertTriangle size={12} color="#ef4444" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
