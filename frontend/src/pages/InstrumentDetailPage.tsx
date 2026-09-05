import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, DepthLevel } from "../api/client";
import { useLivePrices } from "../hooks/useLivePrices";

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function InstrumentDetailPage() {
  const { instrumentKey = "" } = useParams<{ instrumentKey: string }>();

  const { data: instrument, isLoading } = useQuery({
    queryKey: ["instrument", instrumentKey],
    queryFn: () => api.getInstrument(instrumentKey),
    enabled: !!instrumentKey,
  });

  const { data: depthData } = useQuery({
    queryKey: ["instrument-depth", instrumentKey],
    queryFn: () => api.getInstrumentDepth(instrumentKey),
    enabled: !!instrumentKey,
    // Order book can go stale the moment the market closes; poll so a tab
    // left open still notices (the WS tick stream is the fast path while
    // ticks are actually arriving — this is just the fallback).
    refetchInterval: 15000,
  });

  // The book's current levels — replaced wholesale on every update, not
  // accumulated, since (unlike price) an old order book isn't meaningfully
  // "last known" (see backend depth_store.py).
  const [levels, setLevels] = useState<DepthLevel[]>([]);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  useEffect(() => {
    setLevels(depthData?.levels ?? []);
    setUpdatedAt(depthData?.updated_at ?? null);
  }, [depthData]);

  const liveSnapshots = useLivePrices(instrumentKey ? [instrumentKey] : []);
  const live = liveSnapshots[instrumentKey];

  useEffect(() => {
    if (!live?.depth || live.depth.length === 0) return;
    setLevels(live.depth);
    setUpdatedAt(live.ts);
  }, [live]);

  const current = live ?? instrument?.snapshot ?? null;

  return (
    <div className="dashboard">
      <Link to="/" className="back-link">
        ← Back to watchlist
      </Link>

      {isLoading || !instrument ? (
        <p className="empty-state">Loading…</p>
      ) : (
        <>
          <header className="instrument-header">
            <h1>{instrument.trading_symbol}</h1>
            <span className="instrument-name">{instrument.name}</span>
            <span className="instrument-exchange">{instrument.exchange}</span>
          </header>

          <div className="instrument-info-card">
            {current ? (
              <>
                <div className="info-item">
                  <span className="info-label">LTP</span>
                  <span className="info-value">{current.ltp.toFixed(2)}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Prev. close</span>
                  <span className="info-value">{current.close.toFixed(2)}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Change</span>
                  <span className={`info-value ${current.ltp >= current.close ? "positive" : "negative"}`}>
                    {(current.ltp - current.close).toFixed(2)}
                    {" ("}
                    {current.close ? (((current.ltp - current.close) / current.close) * 100).toFixed(2) : "0.00"}%)
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Status</span>
                  <span className={`badge ${current.is_live ? "badge-live" : "badge-closed"}`}>
                    {current.is_live ? "Live" : `Market closed · as of ${formatTime(current.ts)}`}
                  </span>
                </div>
              </>
            ) : (
              <p className="empty-state">No price data yet for this instrument.</p>
            )}
          </div>

          <h2 className="section-title">
            Market depth
            {updatedAt ? ` · as of ${formatTime(updatedAt)}` : ""}
          </h2>
          {levels.length === 0 ? (
            <p className="empty-state">
              No live order-book depth right now — this is only available while the market is
              open (09:15–15:30 IST, weekdays) or in mock mode.
            </p>
          ) : (
            <div className="table-scroll">
              <table className="depth-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Bid Qty</th>
                    <th>Bid</th>
                    <th>Ask</th>
                    <th>Ask Qty</th>
                  </tr>
                </thead>
                <tbody>
                  {levels.map((level, i) => (
                    <tr key={i}>
                      <td className="depth-rank">{i + 1}</td>
                      <td>{level.bid_qty}</td>
                      <td className="bid-price">{level.bid_price.toFixed(2)}</td>
                      <td className="ask-price">{level.ask_price.toFixed(2)}</td>
                      <td>{level.ask_qty}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
