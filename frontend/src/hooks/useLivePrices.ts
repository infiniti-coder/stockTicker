import { useEffect, useRef, useState } from "react";

import { Snapshot, WS_BASE } from "../api/client";

const RECONNECT_DELAY_MS = 2000;

type ServerMessage =
  | { type: "snapshot"; data: Snapshot[] }
  | ({ type: "tick" } & Snapshot);

/**
 * Owns the single browser <-> backend /ws/prices connection and keeps a
 * live instrument_key -> Snapshot map in sync with it. Re-subscribes
 * whenever the watchlist (instrumentKeys) changes, and auto-reconnects on
 * drop (README §3: the backend fans this same feed out to every tab).
 */
export function useLivePrices(instrumentKeys: string[]): Record<string, Snapshot> {
  const [prices, setPrices] = useState<Record<string, Snapshot>>({});
  const wsRef = useRef<WebSocket | null>(null);
  const keysRef = useRef<string[]>(instrumentKeys);
  keysRef.current = instrumentKeys;

  const keysDep = [...instrumentKeys].sort().join(",");

  useEffect(() => {
    let cancelled = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      if (cancelled) return;
      const ws = new WebSocket(`${WS_BASE}/ws/prices`);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ type: "subscribe", instrument_keys: keysRef.current }));
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data) as ServerMessage;
        if (msg.type === "snapshot") {
          setPrices((prev) => {
            const next = { ...prev };
            for (const snap of msg.data) next[snap.instrument_key] = snap;
            return next;
          });
        } else if (msg.type === "tick") {
          const { type: _type, ...snap } = msg;
          setPrices((prev) => ({ ...prev, [snap.instrument_key]: snap }));
        }
      };

      ws.onclose = () => {
        if (cancelled) return;
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "subscribe", instrument_keys: instrumentKeys }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keysDep]);

  return prices;
}
