import { Snapshot } from "../api/client";

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function PriceCell({ snapshot }: { snapshot: Snapshot | null }) {
  if (!snapshot) {
    return <span className="price-cell price-cell-empty">—</span>;
  }

  return (
    <div className="price-cell">
      <div className="price-main">
        <span className="ltp">{snapshot.ltp.toFixed(2)}</span>
        <span className={`badge ${snapshot.is_live ? "badge-live" : "badge-closed"}`}>
          {snapshot.is_live ? "Live" : `Market closed · as of ${formatTime(snapshot.ts)}`}
        </span>
      </div>
      <div className="price-depth">
        <span>
          Bid {snapshot.bid.toFixed(2)} ({snapshot.bid_qty})
        </span>
        <span>
          Ask {snapshot.ask.toFixed(2)} ({snapshot.ask_qty})
        </span>
      </div>
    </div>
  );
}
