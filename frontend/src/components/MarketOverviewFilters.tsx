import { useMemo } from "react";

import { MarketOverviewPeriod, MarketOverviewRegion, MarketOverviewStock } from "../api/client";

const PERIODS: { value: MarketOverviewPeriod; label: string }[] = [
  { value: "1d", label: "1D" },
  { value: "1w", label: "1W" },
  { value: "1m", label: "1M" },
  { value: "6m", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "5y", label: "5Y" },
];

const CURATED_THEMES = ["AI", "Green Energy", "Oil"];

interface Props {
  region: MarketOverviewRegion;
  onRegionChange: (region: MarketOverviewRegion) => void;
  period: MarketOverviewPeriod;
  onPeriodChange: (period: MarketOverviewPeriod) => void;
  category: string;
  onCategoryChange: (category: string) => void;
  stocks: MarketOverviewStock[];
}

export function MarketOverviewFilters({
  region,
  onRegionChange,
  period,
  onPeriodChange,
  category,
  onCategoryChange,
  stocks,
}: Props) {
  const sectors = useMemo(
    () => Array.from(new Set(stocks.map((s) => s.sector).filter((s): s is string => !!s))).sort(),
    [stocks],
  );

  return (
    <div className="market-overview-filters">
      <div className="filter-group" role="group" aria-label="Region">
        {(["india", "world"] as const).map((r) => (
          <button
            key={r}
            type="button"
            className={`filter-toggle ${region === r ? "filter-toggle-active" : ""}`}
            onClick={() => onRegionChange(r)}
          >
            {r === "india" ? "India" : "Worldwide"}
          </button>
        ))}
      </div>

      <div className="filter-group" role="group" aria-label="Period">
        {PERIODS.map((p) => (
          <button
            key={p.value}
            type="button"
            className={`filter-toggle ${period === p.value ? "filter-toggle-active" : ""}`}
            onClick={() => onPeriodChange(p.value)}
          >
            {p.label}
          </button>
        ))}
      </div>

      <select
        className="filter-select"
        value={category}
        onChange={(e) => onCategoryChange(e.target.value)}
        aria-label="Category"
      >
        <option value="all">All categories</option>
        <optgroup label="Themes">
          {CURATED_THEMES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </optgroup>
        <optgroup label="Sectors">
          {sectors.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </optgroup>
      </select>
    </div>
  );
}
