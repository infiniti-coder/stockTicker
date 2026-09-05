import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { api, ChatSource, MarketOverviewRegion } from "../api/client";
import { StreamedAnswer } from "../components/StreamedAnswer";

export function ScreenerPage() {
  const [region, setRegion] = useState<MarketOverviewRegion>("india");
  const [criteria, setCriteria] = useState("");
  const [running, setRunning] = useState(false);
  const [resultText, setResultText] = useState("");
  const [resultSources, setResultSources] = useState<ChatSource[]>([]);
  const [hasRun, setHasRun] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = criteria.trim();
    if (!trimmed || running) return;

    setRunning(true);
    setHasRun(true);
    setResultText("");
    setResultSources([]);

    let text = "";
    try {
      await api.runScreener(
        region,
        trimmed,
        (delta) => {
          text += delta;
          setResultText(text);
        },
        (sources) => setResultSources(sources),
      );
    } catch {
      setResultText("Couldn't reach the screener service. Check that ANTHROPIC_API_KEY is set on the backend.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="dashboard">
      <Link to="/" className="back-link">
        ← Back to market overview
      </Link>

      <header className="dashboard-header">
        <h1>Screener</h1>
      </header>

      <p className="empty-state chat-empty-hint">
        Give it open-ended criteria and it researches on its own — pulling real data, shortlisting, then digging
        deeper on a handful of candidates before ranking a short list. Grounded in this app's own market data and
        real web sources; never a buy/sell recommendation, and a run can take a couple of minutes.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="filter-group screener-region-toggle" role="group" aria-label="Region">
          {(["india", "world"] as const).map((r) => (
            <button
              key={r}
              type="button"
              className={`filter-toggle ${region === r ? "filter-toggle-active" : ""}`}
              onClick={() => setRegion(r)}
              disabled={running}
            >
              {r === "india" ? "India" : "Worldwide"}
            </button>
          ))}
        </div>

        <textarea
          className="screener-criteria"
          value={criteria}
          onChange={(e) => setCriteria(e.target.value)}
          placeholder="e.g. strong 1-year momentum and improving margins, no major negative news in the last month"
          rows={3}
          disabled={running}
        />

        <button type="submit" disabled={running || !criteria.trim()} className="screener-run-button">
          {running ? "Running…" : "Run screen"}
        </button>
      </form>

      {hasRun && (
        <div className="screener-result">
          <h2 className="section-title">Result</h2>
          {running && !resultText ? (
            <p className="empty-state">Pulling real data and researching candidates…</p>
          ) : (
            <StreamedAnswer content={resultText} sources={resultSources} />
          )}
        </div>
      )}
    </div>
  );
}
