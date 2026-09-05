import { getSessionId } from "./session";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
export const WS_BASE = API_BASE.replace(/^http/, "ws");

export interface DepthLevel {
  bid_price: number;
  bid_qty: number;
  ask_price: number;
  ask_qty: number;
}

export interface Snapshot {
  instrument_key: string;
  ltp: number;
  bid: number;
  ask: number;
  bid_qty: number;
  ask_qty: number;
  close: number;
  ts: string;
  is_live: boolean;
  depth?: DepthLevel[];
}

export interface Instrument {
  instrument_key: string;
  trading_symbol: string;
  name: string;
  exchange: string;
}

export interface WatchlistItem {
  instrument_key: string;
  trading_symbol: string;
  name: string;
  snapshot: Snapshot | null;
}

export interface AuthStatus {
  logged_in: boolean;
  is_mock: boolean;
  logged_in_at: string | null;
}

export interface InstrumentDetail {
  instrument_key: string;
  trading_symbol: string;
  name: string;
  exchange: string;
  snapshot: Snapshot | null;
}

export interface DepthResponse {
  instrument_key: string;
  updated_at: string | null;
  levels: DepthLevel[];
}

export type MarketOverviewRegion = "india" | "world";
export type MarketOverviewPeriod = "1d" | "1w" | "1m" | "6m" | "1y" | "5y";
export type MarketOverviewTheme = "AI" | "Green Energy" | "Oil";

export interface MarketOverviewStock {
  symbol: string;
  name: string;
  market_cap: number;
  sector: string | null;
  industry: string | null;
  theme: MarketOverviewTheme | null;
  returns: Record<MarketOverviewPeriod, number | null>;
}

export interface MarketOverviewResponse {
  region: MarketOverviewRegion;
  stocks: MarketOverviewStock[];
}

export interface StockHistoryPoint {
  date: string;
  close: number;
}

export interface StockHistoryResponse {
  symbol: string;
  points: StockHistoryPoint[];
}

export interface ChatSource {
  title: string;
  url: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[];
  created_at: string;
}

/**
 * Reads a fetch Response body as SSE `event:`/`data:` blocks, dispatching
 * "delta" events (`{text}`) and "sources" events (`ChatSource[]`) as they
 * arrive. Shared by postChatMessage and runScreener — both backend
 * endpoints emit the identical wire format. Not EventSource-based —
 * EventSource can't send a POST body or the X-Session-Id header.
 */
async function consumeSSE(
  res: Response,
  onDelta: (text: string) => void,
  onSources: (sources: ChatSource[]) => void,
): Promise<void> {
  if (!res.ok || !res.body) {
    throw new Error(`Request failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      let eventType = "message";
      let data = "";
      for (const line of rawEvent.split("\n")) {
        if (line.startsWith("event: ")) eventType = line.slice(7);
        else if (line.startsWith("data: ")) data = line.slice(6);
      }
      if (!data) continue;

      if (eventType === "delta") {
        onDelta((JSON.parse(data) as { text: string }).text);
      } else if (eventType === "sources") {
        onSources(JSON.parse(data) as ChatSource[]);
      }
    }
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", "X-Session-Id": getSessionId() },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status} ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  authStatus: () => apiFetch<AuthStatus>("/auth/status"),
  logout: () => apiFetch<{ logged_in: boolean }>("/auth/logout", { method: "POST" }),
  loginUrl: () => `${API_BASE}/auth/login`,

  searchInstruments: (q: string) =>
    apiFetch<Instrument[]>(`/instruments/search?q=${encodeURIComponent(q)}`),

  getInstrument: (instrumentKey: string) =>
    apiFetch<InstrumentDetail>(`/instruments/${encodeURIComponent(instrumentKey)}`),
  getInstrumentDepth: (instrumentKey: string) =>
    apiFetch<DepthResponse>(`/instruments/${encodeURIComponent(instrumentKey)}/depth`),

  getWatchlist: () => apiFetch<WatchlistItem[]>("/watchlist"),
  addToWatchlist: (instrument_key: string) =>
    apiFetch<WatchlistItem>("/watchlist", {
      method: "POST",
      body: JSON.stringify({ instrument_key }),
    }),
  removeFromWatchlist: (instrument_key: string) =>
    apiFetch<{ removed: string }>(`/watchlist/${encodeURIComponent(instrument_key)}`, {
      method: "DELETE",
    }),

  getMarketOverview: (region: MarketOverviewRegion) =>
    apiFetch<MarketOverviewResponse>(`/market-overview?region=${region}`),
  getStockHistory: (symbol: string) =>
    apiFetch<StockHistoryResponse>(`/market-overview/history?symbol=${encodeURIComponent(symbol)}`),

  getChatHistory: () => apiFetch<ChatMessage[]>("/chat/messages"),

  postChatMessage: (content: string, onDelta: (text: string) => void, onSources: (sources: ChatSource[]) => void) =>
    fetch(`${API_BASE}/chat/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-Id": getSessionId() },
      body: JSON.stringify({ content }),
    }).then((res) => consumeSSE(res, onDelta, onSources)),

  runScreener: (
    region: MarketOverviewRegion,
    criteria: string,
    onDelta: (text: string) => void,
    onSources: (sources: ChatSource[]) => void,
  ) =>
    fetch(`${API_BASE}/screener/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Session-Id": getSessionId() },
      body: JSON.stringify({ region, criteria }),
    }).then((res) => consumeSSE(res, onDelta, onSources)),
};
