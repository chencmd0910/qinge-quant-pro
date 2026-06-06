"use client";

import PortfolioHeader from "./portfolio-header";
import AllocationPanel from "./allocation-panel";
import CorrelationMatrix from "./correlation-matrix";
import RiskContribution from "./risk-contribution";
import PortfolioKPI from "./portfolio-kpi";

export default function PortfolioLayout() {
  return (
    <div className="h-full flex flex-col gap-4">
      <PortfolioHeader />
      <PortfolioKPI />

      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        {/* Left: Allocation */}
        <div className="col-span-5">
          <AllocationPanel />
        </div>

        {/* Right top: Correlation */}
        <div className="col-span-7 flex flex-col gap-4">
          <CorrelationMatrix />
          <RiskContribution />
        </div>
      </div>
    </div>
  );
}
