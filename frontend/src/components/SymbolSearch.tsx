import { useState } from "react";

import { api, Instrument } from "../api/client";
import { useAddToWatchlist } from "../hooks/useWatchlist";

export function SymbolSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(false);
  const addToWatchlist = useAddToWatchlist();

  async function handleChange(value: string) {
    setQuery(value);
    if (value.trim().length < 1) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const found = await api.searchInstruments(value);
      setResults(found);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="symbol-search">
      <input
        type="text"
        placeholder="Search NSE symbols (e.g. RELIANCE)"
        value={query}
        onChange={(e) => handleChange(e.target.value)}
      />
      {loading && <div className="search-hint">Searching…</div>}
      {results.length > 0 && (
        <ul className="search-results">
          {results.map((inst) => (
            <li key={inst.instrument_key}>
              <button
                onClick={() => {
                  addToWatchlist.mutate(inst.instrument_key);
                  setQuery("");
                  setResults([]);
                }}
              >
                <strong>{inst.trading_symbol}</strong>
                <span>{inst.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
