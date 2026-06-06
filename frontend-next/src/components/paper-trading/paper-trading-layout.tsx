"use client";

import PaperHeader from "./paper-header";
import PaperKPI from "./paper-kpi";
import PositionsTable from "./positions-table";
import TradeLog from "./trade-log";
import EquityCurve from "./equity-curve";
import StrategySwitch from "./strategy-switch";

export default function PaperTradingLayout() {
  return (
    <div className="h-full flex flex-col gap-4">
      <PaperHeader />
      <PaperKPI />
      <StrategySwitch />

      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        {/* Left: Positions */}
        <div className="col-span-5 flex flex-col gap-4">
          <PositionsTable />
        </div>

        {/* Right: Equity + Log */}
        <div className="col-span-7 flex flex-col gap-4">
          <EquityCurve />
          <TradeLog />
        </div>
      </div>
    </div>
  );
}
