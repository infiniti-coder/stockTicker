import { useMemo, useState } from "react";

import { ChatPanel } from "../components/ChatPanel";
import { LoginButton } from "../components/LoginButton";
import { MarketOverviewFilters } from "../components/MarketOverviewFilters";
import { MarketOverviewTreemap } from "../components/MarketOverviewTreemap";
import { SymbolSearch } from "../components/SymbolSearch";
import { WatchlistTable } from "../components/WatchlistTable";
import { useLivePrices } from "../hooks/useLivePrices";
import { useMarketOverview } from "../hooks/useMarketOverview";
import { useWatchlist } from "../hooks/useWatchlist";
import { MarketOverviewPeriod, MarketOverviewRegion } from "../api/client";

const CURATED_THEMES = new Set(["AI", "Green Energy", "Oil"]);

export function Dashboard() {
  const { data: watchlist, isLoading } = useWatchlist();
  const instrumentKeys = (watchlist ?? []).map((item) => item.instrument_key);
  const liveSnapshots = useLivePrices(instrumentKeys);

  const [region, setRegion] = useState<MarketOverviewRegion>("india");
  const [period, setPeriod] = useState<MarketOverviewPeriod>("1d");
  const [category, setCategory] = useState<string>("all");
  const overview = useMarketOverview(region);
  const stocks = overview.data?.stocks ?? [];

  const filteredStocks = useMemo(() => {
    if (category === "all") return stocks;
    if (CURATED_THEMES.has(category)) return stocks.filter((s) => s.theme === category);
    return stocks.filter((s) => s.sector === category);
  }, [stocks, category]);

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <h1>stockTicker</h1>
        <LoginButton />
      </header>

      <div className="dashboard-layout">
        <aside className="watchlist-panel">
          <SymbolSearch />
          {isLoading ? (
            <p className="empty-state">Loading watchlist…</p>
          ) : (
            <div className="table-scroll">
              <WatchlistTable items={watchlist ?? []} liveSnapshots={liveSnapshots} />
            </div>
          )}
        </aside>

        <div className="dashboard-main">
          <section className="market-overview-section">
            <h2 className="section-title">Market overview</h2>
            <MarketOverviewFilters
              region={region}
              onRegionChange={setRegion}
              period={period}
              onPeriodChange={setPeriod}
              category={category}
              onCategoryChange={setCategory}
              stocks={stocks}
            />
            {overview.isLoading ? (
              <p className="empty-state">
                Fetching real market data for {region === "india" ? "India" : "the world"}…
              </p>
            ) : overview.isError ? (
              <p className="empty-state">Couldn't load market data. Try again shortly.</p>
            ) : filteredStocks.length === 0 ? (
              <p className="empty-state">No stocks match this filter.</p>
            ) : (
              <MarketOverviewTreemap stocks={filteredStocks} period={period} />
            )}
          </section>
        </div>

        <ChatPanel />
      </div>
    </div>
  );
}
