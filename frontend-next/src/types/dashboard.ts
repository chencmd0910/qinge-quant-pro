export interface KPIData {
  title: string;
  value: string;
  change: string;
  up: boolean;
}

export interface EquityPoint {
  date: string;
  value: number;
}

export interface Strategy {
  id: string;
  name: string;
  cluster: string;
  annual_return: number;
  sharpe: number;
  alpha: number;
  status: "ACTIVE" | "WATCHLIST" | "RETIRED";
  decay_status: "HEALTHY" | "DEGRADING" | "DEAD" | "RECOVERING";
}

export interface RiskAlert {
  level: "critical" | "warning" | "info";
  title: string;
  desc: string;
  time: string;
}

export interface DashboardData {
  kpis: KPIData[];
  equity_curve: EquityPoint[];
  strategies: Strategy[];
  alerts: RiskAlert[];
}
