import { Link, useLocation, useParams } from "react-router-dom";

import { StockHistoryChart } from "../components/StockHistoryChart";
import { useStockHistory } from "../hooks/useStockHistory";

interface LocationState {
  name?: string;
}

function currencySymbol(symbol: string): string {
  return symbol.endsWith(".NS") ? "₹" : "$";
}

export function MarketStockDetailPage() {
  const { symbol = "" } = useParams<{ symbol: string }>();
  const location = useLocation();
  const name = (location.state as LocationState | null)?.name ?? symbol;

  const { data, isLoading, isError } = useStockHistory(symbol);
  const points = data?.points ?? [];
  const first = points[0];
  const latest = points[points.length - 1];
  const changePct = first && latest && first.close ? ((latest.close - first.close) / first.close) * 100 : null;
  const currency = currencySymbol(symbol);

  return (
    <div className="dashboard">
      <Link to="/" className="back-link">
        ← Back to market overview
      </Link>

      <header className="instrument-header">
        <h1>{symbol}</h1>
        <span className="instrument-name">{name}</span>
      </header>

      {isLoading ? (
        <p className="empty-state">Loading full price history…</p>
      ) : isError || points.length === 0 ? (
        <p className="empty-state">Couldn't load history for {symbol}.</p>
      ) : (
        <>
          <div className="stock-detail-summary">
            <div className="info-item">
              <span className="info-label">Latest close</span>
              <span className="info-value">
                {currency}
                {latest.close.toFixed(2)}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Since inception ({first.date})</span>
              <span className={`info-value ${(changePct ?? 0) >= 0 ? "positive" : "negative"}`}>
                {changePct != null ? `${changePct >= 0 ? "+" : ""}${changePct.toFixed(1)}%` : "—"}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Data points</span>
              <span className="info-value">{points.length.toLocaleString()}</span>
            </div>
          </div>

          <h2 className="section-title">Full price history</h2>
          <StockHistoryChart points={points} currencySymbol={currency} />
        </>
      )}
    </div>
  );
}
