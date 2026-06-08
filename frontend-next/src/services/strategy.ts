import api from "@/lib/axios";

export async function fetchStrategyRegistry() {
  const { data } = await api.get("/api/strategy/list");
  return data;
}

export async function fetchStrategyCode(id: string) {
  const { data } = await api.get(`/api/strategy/${id}`);
  return data;
}

export async function saveStrategyCode(id: string, code: string) {
  const { data } = await api.post(`/api/strategy/${id}/save-code`, { code });
  return data;
}
