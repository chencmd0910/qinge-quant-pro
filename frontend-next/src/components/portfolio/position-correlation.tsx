"use client";

import { useEffect, useState } from "react";
import { GitCompare, AlertTriangle, CheckCircle } from "lucide-react";

interface CorrData {
  codes: string[];
  matrix: any[];
  avg_correlation?: number;
  max_pair?: { a: string; b: string; corr: number };
  concentration_warning?: boolean;
  lookback_days?: number;
}

export default function PositionCorrelation() {
  const [data, setData] = useState<CorrData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/portfolio/correlation")
      .then(r => r.json())
      .then(d => { if (!d.error && d.matrix) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl p-4 animate-pulse" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
        <div className="h-4 w-36 rounded mb-4" style={{ background: "var(--border-color)" }} />
        <div className="h-48 rounded" style={{ background: "var(--border-color)", opacity: 0.3 }} />
      </div>
    );
  }

  if (!data || !data.codes?.length) return null;

  const n = data.codes.length;
  const cellSize = n > 15 ? 18 : 24;
  const labelW = 48;
  const svgW = labelW + n * cellSize + 20;
  const svgH = 30 + n * cellSize + 30;

  const corrColor = (val: number) => {
    const abs = Math.abs(val);
    if (abs < 0.05) return "rgba(148,163,184,0.15)";
    return val > 0
      ? `rgba(239,68,68,${Math.min(abs * 0.9, 0.9).toFixed(2)})`
      : `rgba(59,130,246,${Math.min(abs * 0.9, 0.9).toFixed(2)})`;
  };

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <GitCompare size={14} style={{ color: "var(--accent-blue)" }} />
          <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
            持仓相关性矩阵
          </span>
        </div>
        <div className="flex items-center gap-2">
          {data.concentration_warning ? (
            <div className="flex items-center gap-1 text-[10px]" style={{ color: "#eab308" }}>
              <AlertTriangle size={12} />
              预警
            </div>
          ) : (
            <div className="flex items-center gap-1 text-[10px]" style={{ color: "var(--accent)" }}>
              <CheckCircle size={12} />
              分散
            </div>
          )}
          <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>
            均值 {data.avg_correlation?.toFixed(2) || "--"} · {data.lookback_days || 60}日
          </span>
        </div>
      </div>

      {/* Max pair warning */}
      {data.max_pair && (
        <div className="text-[10px] mb-2 px-2 py-1 rounded" style={{
          color: data.max_pair.corr > 0.7 ? "#eab308" : "var(--text-muted)",
          backgroundColor: data.max_pair.corr > 0.7 ? "rgba(234,179,8,0.08)" : "transparent",
          border: data.max_pair.corr > 0.7 ? "1px solid rgba(234,179,8,0.15)" : "none",
        }}>
          最高相关: {data.max_pair.a}—{data.max_pair.b} = {data.max_pair.corr?.toFixed(2)}
        </div>
      )}

      <div className="overflow-auto">
        <svg viewBox={`0 0 ${svgW} ${svgH}`} style={{ minWidth: 350 }}>
          {/* Column headers */}
          {data.codes.map((code, i) => (
            <text key={`ch-${i}`}
              x={labelW + i * cellSize + cellSize / 2}
              y="16"
              textAnchor="middle"
              fontSize={n > 15 ? "7" : "8"}
              fill="#64748B"
              transform={`rotate(-60, ${labelW + i * cellSize + cellSize / 2}, 16)`}
            >
              {code.slice(-4)}
            </text>
          ))}

          {/* Cells */}
          {data.matrix.map((row: any, i: number) => (
            <g key={`r-${i}`}>
              <text x={labelW - 4} y={30 + i * cellSize + cellSize * 0.65}
                textAnchor="end" fontSize="7" fill="#94a3b8">
                {row.code?.slice(-4) || ""}
              </text>
              {data.codes.map((code: string, j: number) => {
                const val = row.row?.[code] ?? 0;
                const abs = Math.abs(val);
                let fill = "rgba(148,163,184,0.15)";
                if (abs > 0.05) {
                  fill = val > 0
                    ? `rgba(239,68,68,${Math.min(abs * 0.9, 0.9).toFixed(2)})`
                    : `rgba(59,130,246,${Math.min(abs * 0.9, 0.9).toFixed(2)})`;
                }
                return (
                  <g key={`c-${i}-${j}`}>
                    <rect
                      x={labelW + j * cellSize + 1}
                      y={30 + i * cellSize + 1}
                      width={cellSize - 2}
                      height={cellSize - 2}
                      rx={1}
                      fill={fill}
                      stroke={i === j ? "#64748B" : "transparent"}
                      strokeWidth={i === j ? 1 : 0}
                    >
                      <title>{row.code} × {code}: {val.toFixed(3)}</title>
                    </rect>
                  </g>
                );
              })}
            </g>
          ))}

          {/* Legend */}
          <g transform={`translate(${labelW + 4}, ${30 + n * cellSize + 12})`}>
            <rect x="0" y="0" width="10" height="7" rx="1" fill="rgba(239,68,68,0.7)" />
            <text x="14" y="7" fontSize="7" fill="#64748B">+1</text>
            <rect x="26" y="0" width="10" height="7" rx="1" fill="rgba(59,130,246,0.7)" />
            <text x="40" y="7" fontSize="7" fill="#64748B">-1</text>
            <rect x="52" y="0" width="10" height="7" rx="1" fill="rgba(148,163,184,0.15)" stroke="#94a3b8" strokeWidth="0.5" />
            <text x="66" y="7" fontSize="7" fill="#64748B">0</text>
          </g>
        </svg>
      </div>
    </div>
  );
}
