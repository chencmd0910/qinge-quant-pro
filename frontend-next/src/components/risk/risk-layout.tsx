"use client";

import RiskHeader from "./risk-header";
import RiskScore from "./risk-score";
import RiskCategories from "./risk-categories";
import RiskHeatmap from "./risk-heatmap";
import AutoActions from "./auto-actions";
import RiskTimeline from "./risk-timeline";

export default function RiskLayout() {
  return (
    <div className="h-full flex flex-col gap-4">
      <RiskHeader />

      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        {/* Left column */}
        <div className="col-span-4 flex flex-col gap-4">
          <RiskScore />
          <RiskCategories />
        </div>

        {/* Right column */}
        <div className="col-span-8 flex flex-col gap-4">
          <RiskHeatmap />
          <div className="grid grid-cols-2 gap-4">
            <AutoActions />
            <RiskTimeline />
          </div>
        </div>
      </div>
    </div>
  );
}
