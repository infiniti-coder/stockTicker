"""Static ticker universes for the market-overview treemap.

Same role as app/upstox_client/fixtures.py's MOCK_INSTRUMENTS — a fixed
list of symbols to query — except these are real, live-quoted symbols.
No free API reliably screens "top N by market cap", so region membership
is a hand-maintained list; the market cap, sector, and returns behind
each symbol are still fetched live (see service.py). Refresh this list
occasionally by hand if it drifts from reality.
"""

# NIFTY-50-ish large caps, Yahoo Finance's NSE suffix.
INDIA: list[str] = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LT.NS", "KOTAKBANK.NS",
    "AXISBANK.NS", "BAJFINANCE.NS", "HINDUNILVR.NS", "MARUTI.NS", "ASIANPAINT.NS",
    "WIPRO.NS", "SUNPHARMA.NS", "TITAN.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "ADANIENT.NS", "HCLTECH.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "POWERGRID.NS",
    "NTPC.NS", "ONGC.NS", "BAJAJFINSV.NS", "M&M.NS", "TECHM.NS",
    "INDUSINDBK.NS", "JSWSTEEL.NS", "GRASIM.NS", "ADANIPORTS.NS", "CIPLA.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "BPCL.NS", "COALINDIA.NS", "HDFCLIFE.NS",
    "SBILIFE.NS", "DIVISLAB.NS", "BRITANNIA.NS", "HEROMOTOCO.NS", "APOLLOHOSP.NS",
    "TATACONSUM.NS", "UPL.NS", "SHRIRAMFIN.NS",
]

# Global mega caps spanning tech/energy/healthcare/industrials/consumer so
# the theme filters (AI / Green Energy / Oil) have real matches.
WORLD: list[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "JPM", "V",
    "UNH", "XOM", "WMT", "MA", "JNJ", "PG", "HD", "CVX", "MRK", "ABBV",
    "KO", "PEP", "COST", "AVGO", "ORCL", "ADBE", "CRM", "AMD", "INTC", "QCOM",
    "TXN", "NFLX", "DIS", "NKE", "MCD", "TSM", "SHEL", "BP", "TTE", "NEE",
    "ENPH", "FSLR", "RIO", "BHP", "SAP", "ASML", "NVO", "PFE", "ABT", "LIN",
    "HON", "CAT", "GE", "BA", "UPS", "LOW", "SBUX", "IBM", "CSCO", "COP",
]
