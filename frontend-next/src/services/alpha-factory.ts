import api from "@/lib/axios";

export async function fetchAlphaFactory(status: "active" | "watchlist" | "retired") {
  const { data } = await api.get(`/api/alpha_factory?status=${status}`);
  return data;
}

export async function promoteStrategy(id: string, toStatus: string) {
  const { data } = await api.post(`/api/alpha_factory/${id}/promote`, { status: toStatus });
  return data;
}

export async function retireStrategy(id: string, reason: string) {
  const { data } = await api.post(`/api/alpha_factory/${id}/retire`, { reason });
  return data;
}
