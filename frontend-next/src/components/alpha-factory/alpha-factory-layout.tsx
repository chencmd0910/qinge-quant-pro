"use client";

import { useEffect, useState } from "react";
import ActiveColumn from "./active-column";
import WatchlistColumn from "./watchlist-column";
import RetiredColumn from "./retired-column";
import FactoryHeader from "./factory-header";
import api from "@/lib/axios";

export interface StrategyCard {
  id: string;
  name: string;
  version: string;
  sharpe: number;
  alpha: number;
  max_dd: number;
  annual: number;
  live_days: number;
  win_rate: number;
  trades: number;
  last_signal: string;
  status: string;
  decay_status: string;
}

export default function AlphaFactoryLayout() {
  const [active, setActive] = useState<StrategyCard[]>([]);
  const [watchlist, setWatchlist] = useState<StrategyCard[]>([]);
  const [retired, setRetired] = useState<StrategyCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/alpha-factory/dashboard")
      .then(({ data }) => {
        setActive(data.active?.strategies || []);
        setWatchlist(data.watchlist?.strategies || []);
        setRetired(data.retired?.strategies || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // 晋升：观察 → 活跃
  const promote = (id: string) => {
    const item = watchlist.find((s) => s.id === id);
    if (!item) return;
    setWatchlist((prev) => prev.filter((s) => s.id !== id));
    setActive((prev) => [{ ...item, status: "ACTIVE" }, ...prev]);
  };

  // 退役：活跃 → 退役 / 观察 → 退役
  const retire = (id: string) => {
    let item = active.find((s) => s.id === id);
    if (item) {
      setActive((prev) => prev.filter((s) => s.id !== id));
      const retiredCard: StrategyCard = { ...item, status: "RETIRED" as const };
      setRetired((prev) => [retiredCard, ...prev]);
      return;
    }
    item = watchlist.find((s) => s.id === id);
    if (item) {
      setWatchlist((prev) => prev.filter((s) => s.id !== id));
      const retiredCard: StrategyCard = { ...item, status: "RETIRED" as const };
      setRetired((prev) => [retiredCard, ...prev]);
    }
  };

  return (
    <div className="h-full flex flex-col gap-4">
      <FactoryHeader activeCount={active.length} watchCount={watchlist.length} retiredCount={retired.length} />
      <div className="flex-1 grid grid-cols-12 gap-4 min-h-0">
        <div className="col-span-4">
          <ActiveColumn
            strategies={active}
            loading={loading}
            onRetire={retire}
          />
        </div>
        <div className="col-span-4">
          <WatchlistColumn
            strategies={watchlist}
            loading={loading}
            onPromote={promote}
            onRetire={retire}
          />
        </div>
        <div className="col-span-4">
          <RetiredColumn strategies={retired} loading={loading} />
        </div>
      </div>
    </div>
  );
}
