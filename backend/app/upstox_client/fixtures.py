from .base import Instrument

# A handful of large-cap NSE symbols, enough to exercise search/watchlist/feed
# end-to-end without needing the real (gzip'd, multi-MB) instrument master.
MOCK_INSTRUMENTS: list[Instrument] = [
    Instrument("NSE_EQ|MOCK-RELIANCE", "RELIANCE", "Reliance Industries Ltd"),
    Instrument("NSE_EQ|MOCK-TCS", "TCS", "Tata Consultancy Services Ltd"),
    Instrument("NSE_EQ|MOCK-INFY", "INFY", "Infosys Ltd"),
    Instrument("NSE_EQ|MOCK-HDFCBANK", "HDFCBANK", "HDFC Bank Ltd"),
    Instrument("NSE_EQ|MOCK-ICICIBANK", "ICICIBANK", "ICICI Bank Ltd"),
    Instrument("NSE_EQ|MOCK-SBIN", "SBIN", "State Bank of India"),
    Instrument("NSE_EQ|MOCK-ITC", "ITC", "ITC Ltd"),
    Instrument("NSE_EQ|MOCK-LT", "LT", "Larsen & Toubro Ltd"),
    Instrument("NSE_EQ|MOCK-KOTAKBANK", "KOTAKBANK", "Kotak Mahindra Bank Ltd"),
    Instrument("NSE_EQ|MOCK-AXISBANK", "AXISBANK", "Axis Bank Ltd"),
    Instrument("NSE_EQ|MOCK-BAJFINANCE", "BAJFINANCE", "Bajaj Finance Ltd"),
    Instrument("NSE_EQ|MOCK-BHARTIARTL", "BHARTIARTL", "Bharti Airtel Ltd"),
    Instrument("NSE_EQ|MOCK-HINDUNILVR", "HINDUNILVR", "Hindustan Unilever Ltd"),
    Instrument("NSE_EQ|MOCK-MARUTI", "MARUTI", "Maruti Suzuki India Ltd"),
    Instrument("NSE_EQ|MOCK-ASIANPAINT", "ASIANPAINT", "Asian Paints Ltd"),
    Instrument("NSE_EQ|MOCK-WIPRO", "WIPRO", "Wipro Ltd"),
    Instrument("NSE_EQ|MOCK-SUNPHARMA", "SUNPHARMA", "Sun Pharmaceutical Industries Ltd"),
    Instrument("NSE_EQ|MOCK-TITAN", "TITAN", "Titan Company Ltd"),
    Instrument("NSE_EQ|MOCK-TATAMOTORS", "TATAMOTORS", "Tata Motors Ltd"),
    Instrument("NSE_EQ|MOCK-TATASTEEL", "TATASTEEL", "Tata Steel Ltd"),
]

# Deterministic base close price per symbol, purely so the mock feed has a
# plausible anchor to random-walk around.
MOCK_BASE_PRICE: dict[str, float] = {
    "NSE_EQ|MOCK-RELIANCE": 2950.0,
    "NSE_EQ|MOCK-TCS": 4150.0,
    "NSE_EQ|MOCK-INFY": 1850.0,
    "NSE_EQ|MOCK-HDFCBANK": 1650.0,
    "NSE_EQ|MOCK-ICICIBANK": 1250.0,
    "NSE_EQ|MOCK-SBIN": 830.0,
    "NSE_EQ|MOCK-ITC": 470.0,
    "NSE_EQ|MOCK-LT": 3600.0,
    "NSE_EQ|MOCK-KOTAKBANK": 1780.0,
    "NSE_EQ|MOCK-AXISBANK": 1150.0,
    "NSE_EQ|MOCK-BAJFINANCE": 7200.0,
    "NSE_EQ|MOCK-BHARTIARTL": 1600.0,
    "NSE_EQ|MOCK-HINDUNILVR": 2450.0,
    "NSE_EQ|MOCK-MARUTI": 12800.0,
    "NSE_EQ|MOCK-ASIANPAINT": 2900.0,
    "NSE_EQ|MOCK-WIPRO": 550.0,
    "NSE_EQ|MOCK-SUNPHARMA": 1780.0,
    "NSE_EQ|MOCK-TITAN": 3400.0,
    "NSE_EQ|MOCK-TATAMOTORS": 950.0,
    "NSE_EQ|MOCK-TATASTEEL": 165.0,
}
