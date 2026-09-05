import { Link } from "react-router-dom";

import { Snapshot, WatchlistItem } from "../api/client";
import { useRemoveFromWatchlist } from "../hooks/useWatchlist";
import { PriceCell } from "./PriceCell";

interface Props {
  items: WatchlistItem[];
  liveSnapshots: Record<string, Snapshot>;
}

export function WatchlistTable({ items, liveSnapshots }: Props) {
  const removeFromWatchlist = useRemoveFromWatchlist();

  if (items.length === 0) {
    return <p className="empty-state">No symbols yet — search above to add one.</p>;
  }

  return (
    <table className="watchlist-table">
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Price</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {items.map((item) => {
          const snapshot = liveSnapshots[item.instrument_key] ?? item.snapshot;
          return (
            <tr key={item.instrument_key}>
              <td className="symbol-cell">
                <Link to={`/instrument/${encodeURIComponent(item.instrument_key)}`}>
                  {item.trading_symbol}
                </Link>
              </td>
              <td>
                <PriceCell snapshot={snapshot} />
              </td>
              <td>
                <button
                  className="remove-button"
                  onClick={() => removeFromWatchlist.mutate(item.instrument_key)}
                  aria-label={`Remove ${item.trading_symbol}`}
                >
                  ×
                </button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
