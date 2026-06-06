import api from "@/lib/axios";

export async function fetchBacktestResults() {
  const { data } = await api.get("/api/backtest/result/latest");
  return data;
}

export async function runBacktest(strategyId: string, params?: Record<string, any>) {
  const { data } = await api.post(`/api/backtest/run`, { strategy_id: strategyId, ...params });
  return data;
}
