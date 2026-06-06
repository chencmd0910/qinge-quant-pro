import { create } from "zustand";
import type { DashboardData } from "@/types/dashboard";

interface DashboardStore {
  data: DashboardData | null;
  loading: boolean;
  error: string | null;
  setData: (data: DashboardData) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  data: null,
  loading: false,
  error: null,
  setData: (data) => set({ data }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
