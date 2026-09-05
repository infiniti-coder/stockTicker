import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

/** Full daily-close history from inception, for a single symbol. */
export function useStockHistory(symbol: string) {
  return useQuery({
    queryKey: ["stock-history", symbol],
    queryFn: () => api.getStockHistory(symbol),
    enabled: !!symbol,
    staleTime: 5 * 60 * 1000,
  });
}
