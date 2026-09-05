import { useQuery } from "@tanstack/react-query";

import { api, MarketOverviewRegion } from "../api/client";

/**
 * One fetch per region (~10-15s: real historical data + sector lookups for
 * every stock in the universe, see backend/app/market_overview/service.py).
 * Period and theme are filtered client-side from this same payload — only
 * switching region hits the network again.
 */
export function useMarketOverview(region: MarketOverviewRegion) {
  return useQuery({
    queryKey: ["market-overview", region],
    queryFn: () => api.getMarketOverview(region),
    staleTime: 0,
  });
}
