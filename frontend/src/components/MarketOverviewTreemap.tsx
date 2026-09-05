import { useLayoutEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { MarketOverviewPeriod, MarketOverviewStock } from "../api/client";

interface Rect {
  stock: MarketOverviewStock;
  x: number;
  y: number;
  w: number;
  h: number;
}

// Binary-split treemap: recursively splits the item list in two at
// whichever index balances cumulative market_cap closest to 50/50, then
// splits the rectangle along its longer axis in that same proportion.
function layoutTreemap(items: MarketOverviewStock[], x: number, y: number, w: number, h: number, out: Rect[]): void {
  if (items.length === 0) return;
  if (items.length === 1) {
    out.push({ stock: items[0], x, y, w, h });
    return;
  }
  const total = items.reduce((s, i) => s + i.market_cap, 0);
  let acc = 0;
  let splitIdx = 1;
  let bestDiff = Infinity;
  for (let k = 1; k < items.length; k++) {
    acc += items[k - 1].market_cap;
    const diff = Math.abs(acc - total / 2);
    if (diff < bestDiff) {
      bestDiff = diff;
      splitIdx = k;
    }
  }
  const left = items.slice(0, splitIdx);
  const right = items.slice(splitIdx);
  const leftSum = left.reduce((s, i) => s + i.market_cap, 0);
  const frac = total > 0 ? leftSum / total : 0.5;
  if (w >= h) {
    const leftW = w * frac;
    layoutTreemap(left, x, y, leftW, h, out);
    layoutTreemap(right, x + leftW, y, w - leftW, h, out);
  } else {
    const topH = h * frac;
    layoutTreemap(left, x, y, w, topH, out);
    layoutTreemap(right, x, y + topH, w, h - topH, out);
  }
}

// --green/--red from styles.css, ramped toward a neutral gray midpoint by
// |return|, capped at 8% so a single outlier doesn't wash out the rest.
const GREEN: [number, number, number] = [51, 192, 122];
const RED: [number, number, number] = [224, 85, 92];
const NEUTRAL: [number, number, number] = [42, 47, 58];
const MAX_MAGNITUDE = 8;

function returnColor(pct: number | null): string {
  if (pct == null) return "rgb(42,47,58)";
  const t = Math.min(Math.abs(pct), MAX_MAGNITUDE) / MAX_MAGNITUDE;
  const pole = pct >= 0 ? GREEN : RED;
  const [r, g, b] = NEUTRAL.map((n, i) => Math.round(n + (pole[i] - n) * t));
  return `rgb(${r},${g},${b})`;
}

// Yahoo returns market cap in the listing's local currency, not USD — NSE
// symbols (.NS) come back in INR. Approximate by symbol suffix since the
// backend doesn't currently pass currency through.
function currencySymbol(symbol: string): string {
  return symbol.endsWith(".NS") ? "₹" : "$";
}

function formatMarketCap(v: number, symbol: string): string {
  const c = currencySymbol(symbol);
  if (v >= 1e12) return `${c}${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `${c}${(v / 1e9).toFixed(1)}B`;
  return `${c}${(v / 1e6).toFixed(0)}M`;
}

function formatReturn(pct: number | null): string {
  if (pct == null) return "—";
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

interface Props {
  stocks: MarketOverviewStock[];
  period: MarketOverviewPeriod;
}

export function MarketOverviewTreemap({ stocks, period }: Props) {
  const navigate = useNavigate();
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const [hovered, setHovered] = useState<{ stock: MarketOverviewStock; x: number; y: number } | null>(null);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) setSize({ w: entry.contentRect.width, h: entry.contentRect.height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const sorted = [...stocks].sort((a, b) => b.market_cap - a.market_cap);
  const rects: Rect[] = [];
  if (size.w > 0 && size.h > 0) {
    layoutTreemap(sorted, 0, 0, size.w, size.h, rects);
  }

  return (
    <div className="market-overview-treemap-wrap">
      <div className="market-overview-treemap" ref={containerRef}>
        {rects.map(({ stock, x, y, w, h }) => {
          const pct = stock.returns[period];
          const area = w * h;
          const showFull = area > 1800 && w > 44 && h > 30;
          const showCompact = !showFull && area > 260 && w > 20 && h > 12;
          const nameSize = Math.max(9.5, Math.min(15, w / 10));
          return (
            <div
              key={stock.symbol}
              className="treemap-cell"
              style={{ left: x, top: y, width: w, height: h, background: returnColor(pct) }}
              onMouseMove={(e) => setHovered({ stock, x: e.clientX, y: e.clientY })}
              onMouseLeave={() => setHovered(null)}
              onClick={() => navigate(`/market/${encodeURIComponent(stock.symbol)}`, { state: { name: stock.name } })}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  navigate(`/market/${encodeURIComponent(stock.symbol)}`, { state: { name: stock.name } });
                }
              }}
            >
              {showFull && (
                <>
                  <span className="treemap-cell-name" style={{ fontSize: nameSize }}>
                    {stock.symbol}
                  </span>
                  <span className="treemap-cell-value" style={{ fontSize: Math.max(9.5, nameSize - 2) }}>
                    {formatMarketCap(stock.market_cap, stock.symbol)} &middot; {formatReturn(pct)}
                  </span>
                </>
              )}
              {showCompact && (
                <span className="treemap-cell-name treemap-cell-name-compact" style={{ fontSize: Math.min(11, w / 6) }}>
                  {stock.symbol.replace(/\.NS$/, "")}
                </span>
              )}
            </div>
          );
        })}
      </div>
      {hovered && (
        <div className="treemap-tooltip" style={{ left: hovered.x + 14, top: hovered.y + 14 }}>
          <div className="treemap-tooltip-name">
            {hovered.stock.name} ({hovered.stock.symbol})
          </div>
          <div className="treemap-tooltip-row">
            Market cap: {formatMarketCap(hovered.stock.market_cap, hovered.stock.symbol)}
          </div>
          <div className="treemap-tooltip-row">
            {period.toUpperCase()} return: {formatReturn(hovered.stock.returns[period])}
          </div>
          {hovered.stock.theme && <div className="treemap-tooltip-row">Theme: {hovered.stock.theme}</div>}
          {hovered.stock.sector && <div className="treemap-tooltip-row">Sector: {hovered.stock.sector}</div>}
        </div>
      )}
    </div>
  );
}
