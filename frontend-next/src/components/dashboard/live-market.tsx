"use client";

import { useEffect, useState, useRef } from "react";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

interface LiveData {
  index: {
    sh: { value?: number; change_pct?: number };
    sz: { value?: number; change_pct?: number };
    cy: { value?: number; change_pct?: number };
  };
  overview?: {
    up?: number;
    down?: number;
    date?: string;
  };
  ts: number;
}

export function useLiveMarket() {
  const [data, setData] = useState<LiveData | null>(null);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    function connect() {
      const es = new EventSource("/api/market/stream");
      eventSourceRef.current = es;

      es.onopen = () => setConnected(true);
      es.onmessage = (event) => {
        try {
          const d = JSON.parse(event.data);
          if (d.type === "market_update") {
            setData(d);
          }
        } catch {}
      };
      es.onerror = () => {
        setConnected(false);
        es.close();
        // Reconnect after 5 seconds
        setTimeout(connect, 5000);
      };
    }

    connect();
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  return { data, connected };
}

export function LiveIndicator() {
  const { data, connected } = useLiveMarket();

  if (!data) {
    return (
      <div className="flex items-center gap-1.5 text-[10px]" style={{ color: "var(--text-muted)" }}>
        <Activity size={10} className="animate-pulse" />
        <span>Connecting...</span>
      </div>
    );
  }

  const sh = data.index?.sh;
  const up = data.overview?.up || 0;
  const down = data.overview?.down || 0;

  return (
    <div className="flex items-center gap-3 text-[10px]">
      <span
        className="flex items-center gap-1 font-mono"
        style={{ color: (sh?.change_pct || 0) >= 0 ? "#22c55e" : "#ef4444" }}
      >
        {(sh?.change_pct || 0) >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
        SSE {(sh?.value || 0).toFixed(0)} {(sh?.change_pct || 0) >= 0 ? "+" : ""}{(sh?.change_pct || 0).toFixed(1)}%
      </span>
      <span className="flex items-center gap-1" style={{ color: "var(--text-muted)" }}>
        <span style={{ color: "#22c55e" }}>↑{up}</span>
        <span style={{ color: "#ef4444" }}>↓{down}</span>
      </span>
      <span className="flex items-center gap-1">
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: connected ? "#22c55e" : "#ef4444" }}
        />
        <span style={{ color: connected ? "#22c55e" : "#ef4444" }}>
          {connected ? "LIVE" : "OFF"}
        </span>
      </span>
    </div>
  );
}
