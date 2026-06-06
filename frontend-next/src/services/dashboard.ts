import api from "@/lib/axios";
import type { DashboardData } from "@/types/dashboard";

export async function getDashboard(): Promise<DashboardData> {
  const { data } = await api.get("/api/dashboard/summary");
  return data;
}

export async function getBacktestResult(id: string = "latest") {
  const { data } = await api.get(`/api/backtest/result/${id}`);
  return data;
}

export async function getAlphaFactory() {
  const { data } = await api.get("/api/alpha-factory/dashboard");
  return data;
}
