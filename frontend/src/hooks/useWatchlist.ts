import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

const WATCHLIST_KEY = ["watchlist"];

export function useWatchlist() {
  return useQuery({ queryKey: WATCHLIST_KEY, queryFn: api.getWatchlist });
}

export function useAddToWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (instrumentKey: string) => api.addToWatchlist(instrumentKey),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: WATCHLIST_KEY }),
  });
}

export function useRemoveFromWatchlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (instrumentKey: string) => api.removeFromWatchlist(instrumentKey),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: WATCHLIST_KEY }),
  });
}
