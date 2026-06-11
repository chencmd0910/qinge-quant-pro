"use client";

import { useEffect, useState } from "react";
import { GitBranch } from "lucide-react";

interface CorrelationData {
  factors: string[];
  matrix: number[][];
}

export default function FactorCorrelation() {
  const [data, setData] = useState<CorrelationData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v25/barra-risk")
      .then(r => r.json())
      .then(d => {
        if (d?.factor_correlation) setData(d.factor_correlation);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl p-6 animate-pulse" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
        <div className="h-4 w-32 rounded mb-4" style={{ background: "var(--border-color)" }} />
        <div className="h-48 rounded" style={{ background: "var(--border-color)", opacity: 0.3 }} />
      </div>
    );
  }

  if (!data || !data.factors?.length) return null;

  const n = data.factors.length;
  const cellSize = 28;
  const labelW = 70;
  const svgW = labelW + n * cellSize + 20;
  const svgH = 30 + n * cellSize + 30;

  const corrColor = (val: number) => {
    const abs = Math.abs(val);
    if (abs < 0.05) return "rgba(148,163,184,0.15)";
    return val > 0
      ? `rgba(239,68,68,${(abs * 0.85).toFixed(2)})`
      : `rgba(59,130,246,${(abs * 0.85).toFixed(2)})`;
  };

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: "var(--bg-card)", border: "1px solid var(--border-color)" }}>
      <div className="flex items-center gap-2 mb-3">
        <GitBranch size={14} style={{ color: "var(--accent)" }} />
        <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
          因子相关性矩阵
        </span>
      </div>

      <div className="overflow-auto">
        <svg viewBox={`0 0 ${svgW} ${svgH}`} style={{ minWidth: 400 }}>
          {/* Column labels */}
          {data.factors.map((f, i) => (
            <text key={`ch-${i}`}
              x={labelW + i * cellSize + cellSize / 2}
              y="16"
              textAnchor="middle"
              fontSize="8"
              fill="#64748B"
              transform={`rotate(-45, ${labelW + i * cellSize + cellSize / 2}, 16)`}
            >
              {f.replace("momentum_composite","动合").replace("volume_composite","量合").replace("volatility_composite","波合").replace("money_flow","资金流").replace("no_","").slice(0, 6)}
            </text>
          ))}

          {/* Cells + row labels */}
          {data.matrix.map((row, i) => (
            <g key={`r-${i}`}>
              <text x={labelW - 6} y={30 + i * cellSize + cellSize * 0.65}
                textAnchor="end" fontSize="8" fill="#94a3b8">
                {data.factors[i].replace("momentum_composite","动合").replace("volume_composite","量合").replace("volatility_composite","波合").replace("money_flow","资金流").replace("no_","").slice(0, 8)}
              </text>
              {row.map((val, j) => (
                <g key={`c-${i}-${j}`}>
                  <rect
                    x={labelW + j * cellSize + 2}
                    y={30 + i * cellSize + 2}
                    width={cellSize - 4}
                    height={cellSize - 4}
                    rx={2}
                    fill={corrColor(val)}
                    stroke={i === j ? "#64748B" : "transparent"}
                    strokeWidth={i === j ? 1.5 : 0}
                  />
                  <text
                    x={labelW + j * cellSize + cellSize / 2}
                    y={30 + i * cellSize + cellSize * 0.65}
                    textAnchor="middle"
                    fontSize={8}
                    fill={Math.abs(val) > 0.7 ? "#fff" : "#e2e8f0"}
                    fontWeight={Math.abs(val) > 0.7 ? "bold" : "normal"}
                  >
                    {val.toFixed(2)}
                  </text>
                </g>
              ))}
            </g>
          ))}

          {/* Legend */}
          <g transform={`translate(${labelW + 4}, ${30 + n * cellSize + 12})`}>
            <rect x="0" y="0" width="12" height="8" rx="1" fill="rgba(239,68,68,0.7)" />
            <text x="16" y="8" fontSize="8" fill="#64748B">+1</text>
            <rect x="32" y="0" width="12" height="8" rx="1" fill="rgba(59,130,246,0.7)" />
            <text x="48" y="8" fontSize="8" fill="#64748B">-1</text>
            <rect x="64" y="0" width="12" height="8" rx="1" fill="rgba(148,163,184,0.15)" stroke="#94a3b8" strokeWidth="0.5" />
            <text x="80" y="8" fontSize="8" fill="#64748B">~0</text>
          </g>
        </svg>
      </div>
    </div>
  );
}
