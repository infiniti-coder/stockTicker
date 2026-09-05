import { Route, Routes } from "react-router-dom";

import { Dashboard } from "./pages/Dashboard";
import { InstrumentDetailPage } from "./pages/InstrumentDetailPage";
import { MarketStockDetailPage } from "./pages/MarketStockDetailPage";
import { ScreenerPage } from "./pages/ScreenerPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/instrument/:instrumentKey" element={<InstrumentDetailPage />} />
      <Route path="/market/:symbol" element={<MarketStockDetailPage />} />
      <Route path="/screener" element={<ScreenerPage />} />
    </Routes>
  );
}
