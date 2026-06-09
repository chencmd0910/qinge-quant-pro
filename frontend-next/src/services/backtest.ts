import api from "@/lib/axios";

// ── Types ──

export interface RealBacktestParams {
  start?: string;
  end?: string;
  cash?: number;
  top_n?: number;
  rebalance?: string;
  stop_loss?: number;
  commission?: number;
  slippage?: number;
  ranking_factor?: string;
  strategy_id?: string;
}

export interface RealBacktestResult {
  strategy_id: string;
  start_date: string;
  end_date: string;
  data_source: string;
  config: Record<string, any>;
  metrics: {
    total_return: number;
    annual_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    alpha?: number;
    calmar_ratio?: number;
    trade_count?: number;
  };
  equity_curve: { date: string; value: number }[];
  trades: { date: string; side: string; symbol: string; price: number; quantity: number; amount: number; reason: string }[];
  created_at: string;
}

export async function fetchBacktestResults() {
  const { data } = await api.get("/api/backtest/result/latest");
  return data;
}

export async function runBacktest(strategyId: string, params?: Record<string, any>) {
  const { data } = await api.post(`/api/backtest/run`, { strategy_id: strategyId, ...params });
  return data;
}

export async function runRealBacktest(params: RealBacktestParams): Promise<RealBacktestResult> {
  const { data } = await api.post("/api/backtest/run-real", params);
  return data;
}
