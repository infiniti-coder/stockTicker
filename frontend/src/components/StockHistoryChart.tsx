import { PointerEvent, useLayoutEffect, useMemo, useRef, useState } from "react";

import { StockHistoryPoint } from "../api/client";

interface Props {
  points: StockHistoryPoint[];
  currencySymbol: string;
}

const PADDING = { top: 16, right: 16, bottom: 28, left: 64 };
const LINE_COLOR = "#4f8cff"; // --accent — single series, sequential job (see dataviz skill), not a polarity encoding
const GRID_STEPS = 4;
const X_LABEL_COUNT = 6;

function formatPrice(v: number, currencySymbol: string): string {
  if (v >= 1000) return `${currencySymbol}${(v / 1000).toFixed(1)}k`;
  return `${currencySymbol}${v.toFixed(v < 10 ? 2 : 0)}`;
}

export function StockHistoryChart({ points, currencySymbol }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

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

  const { minClose, maxClose } = useMemo(() => {
    if (points.length === 0) return { minClose: 0, maxClose: 1 };
    let min = Infinity;
    let max = -Infinity;
    for (const p of points) {
      if (p.close < min) min = p.close;
      if (p.close > max) max = p.close;
    }
    return { minClose: min, maxClose: max };
  }, [points]);

  const innerW = Math.max(0, size.w - PADDING.left - PADDING.right);
  const innerH = Math.max(0, size.h - PADDING.top - PADDING.bottom);

  const xFor = (i: number) => PADDING.left + (points.length > 1 ? (i / (points.length - 1)) * innerW : 0);
  const yFor = (close: number) => {
    const range = maxClose - minClose || 1;
    return PADDING.top + innerH - ((close - minClose) / range) * innerH;
  };

  const pathD = useMemo(() => {
    if (points.length === 0 || innerW <= 0) return "";
    return points.map((p, i) => `${i === 0 ? "M" : "L"}${xFor(i).toFixed(1)},${yFor(p.close).toFixed(1)}`).join(" ");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points, innerW, innerH]);

  const gridLines = Array.from({ length: GRID_STEPS + 1 }, (_, i) => {
    const value = minClose + ((maxClose - minClose) * i) / GRID_STEPS;
    return { value, y: yFor(value) };
  });

  const xLabels =
    points.length > 0
      ? Array.from({ length: X_LABEL_COUNT }, (_, i) => {
          const idx = Math.round((i / (X_LABEL_COUNT - 1)) * (points.length - 1));
          return { idx, x: xFor(idx), date: points[idx].date };
        })
      : [];

  function handlePointerMove(e: PointerEvent<SVGRectElement>) {
    if (points.length === 0 || innerW <= 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / innerW));
    setHoverIdx(Math.round(frac * (points.length - 1)));
  }

  const hovered = hoverIdx != null ? points[hoverIdx] : null;
  const latest = points[points.length - 1];
  const tooltipLeft = hoverIdx != null ? Math.min(xFor(hoverIdx), size.w - 130) : 0;

  return (
    <div className="stock-history-chart" ref={containerRef}>
      {size.w > 0 && size.h > 0 && points.length > 0 && (
        <svg width={size.w} height={size.h}>
          {gridLines.map((g, i) => (
            <g key={i}>
              <line x1={PADDING.left} x2={size.w - PADDING.right} y1={g.y} y2={g.y} className="chart-gridline" />
              <text x={PADDING.left - 8} y={g.y} className="chart-axis-label" textAnchor="end" dominantBaseline="middle">
                {formatPrice(g.value, currencySymbol)}
              </text>
            </g>
          ))}
          {xLabels.map((l, i) => (
            <text key={i} x={l.x} y={size.h - 6} className="chart-axis-label" textAnchor="middle">
              {l.date.slice(0, 4)}
            </text>
          ))}
          <path d={pathD} className="chart-line" stroke={LINE_COLOR} fill="none" />
          {latest && (
            <circle
              cx={xFor(points.length - 1)}
              cy={yFor(latest.close)}
              r={5}
              fill={LINE_COLOR}
              stroke="var(--panel)"
              strokeWidth={2}
            />
          )}
          {hovered && hoverIdx != null && (
            <>
              <line
                x1={xFor(hoverIdx)}
                x2={xFor(hoverIdx)}
                y1={PADDING.top}
                y2={size.h - PADDING.bottom}
                className="chart-crosshair"
              />
              <circle cx={xFor(hoverIdx)} cy={yFor(hovered.close)} r={4} fill={LINE_COLOR} stroke="var(--panel)" strokeWidth={2} />
            </>
          )}
          <rect
            x={PADDING.left}
            y={PADDING.top}
            width={innerW}
            height={innerH}
            fill="transparent"
            onPointerMove={handlePointerMove}
            onPointerLeave={() => setHoverIdx(null)}
          />
        </svg>
      )}
      {hovered && (
        <div className="chart-tooltip" style={{ left: tooltipLeft }}>
          <div className="chart-tooltip-date">{hovered.date}</div>
          <div className="chart-tooltip-value">{formatPrice(hovered.close, currencySymbol)}</div>
        </div>
      )}
    </div>
  );
}
