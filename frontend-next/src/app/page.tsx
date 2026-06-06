import QuantLayout from "@/components/layout/quant-layout";
import KPIGrid from "@/components/dashboard/kpi-card";
import EquityChart from "@/components/dashboard/equity-chart";
import StrategyMonitor from "@/components/dashboard/strategy-monitor";
import RiskAlert from "@/components/dashboard/risk-alert";
import AIInsights from "@/components/dashboard/ai-insights";

export default function Page() {
  return (
    <QuantLayout>
      <div className="space-y-6">
        <KPIGrid />
        <EquityChart />
        <div className="grid grid-cols-2 gap-6">
          <StrategyMonitor />
          <AIInsights />
        </div>
        <RiskAlert />
      </div>
    </QuantLayout>
  );
}
