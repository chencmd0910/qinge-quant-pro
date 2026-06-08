"use client";

import { useState, useCallback } from "react";
import PaperHeader from "./paper-header";
import PaperKPI from "./paper-kpi";
import PositionsTable from "./positions-table";
import TradeLog from "./trade-log";
import EquityCurve from "./equity-curve";
import StrategySwitch from "./strategy-switch";

export default function PaperTradingLayout() {
  const [refreshKey, setRefreshKey] = useState(0);
  const handleRefresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  return (
    <div className="h-full flex flex-col gap-4">
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
