import KPIGrid from "@/components/dashboard/kpi-card";
import EquityChart from "@/components/dashboard/equity-chart";
import StrategyMonitor from "@/components/dashboard/strategy-monitor";
import RiskAlert from "@/components/dashboard/risk-alert";
import AIInsights from "@/components/dashboard/ai-insights";

export default function Page() {
  return (
    <div className="space-y-4">
      <KPIGrid />
      <EquityChart />
      <StrategyMonitor />
      <div className="grid grid-cols-2 gap-4">
        <AIInsights />
        <RiskAlert />
      </div>
    </div>
  );
}
