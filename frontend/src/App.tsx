import { Route, Routes } from "react-router-dom";

import { Dashboard } from "./pages/Dashboard";
import { InstrumentDetailPage } from "./pages/InstrumentDetailPage";
import { MarketStockDetailPage } from "./pages/MarketStockDetailPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/instrument/:instrumentKey" element={<InstrumentDetailPage />} />
      <Route path="/market/:symbol" element={<MarketStockDetailPage />} />
    </Routes>
  );
}
