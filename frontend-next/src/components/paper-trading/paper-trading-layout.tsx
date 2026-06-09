"use client";

import { useState, useCallback, useEffect } from "react";
import PaperHeader from "./paper-header";
import PaperKPI from "./paper-kpi";
import PositionsTable from "./positions-table";
import TradeLog from "./trade-log";
import EquityCurve from "./equity-curve";
import StrategySwitch from "./strategy-switch";
import { AlertCircle } from "lucide-react";

export default function PaperTradingLayout() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const handleRefresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    // 仅首次检查：后端是否存活
    fetch("/api/paper-trading/summary")
      .then(r => { if (!r.ok) setError("后端服务连接失败，请检查服务器状态"); })
      .catch(() => setError("无法连接后端服务，请确认服务已启动"));
  }, []);

  return (
    <div className="h-full flex flex-col gap-4">
      {error && (
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-500/30 bg-red-500/10 text-red-400 text-xs">
          <AlertCircle size={14} />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-slate-500 hover:text-slate-300">✕</button>
        </div>
      )}
      <PaperHeader onRefresh={handleRefresh} />
      <PaperKPI key={`kpi-${refreshKey}`} />
      <StrategySwitch />

      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        {/* Left: Positions */}
        <div className="col-span-5 flex flex-col gap-4">
          <PositionsTable key={`pos-${refreshKey}`} />
        </div>

        {/* Right: Equity + Log */}
        <div className="col-span-7 flex flex-col gap-4">
          <EquityCurve key={`eq-${refreshKey}`} />
          <TradeLog key={`log-${refreshKey}`} />
        </div>
      </div>
    </div>
  );
}
