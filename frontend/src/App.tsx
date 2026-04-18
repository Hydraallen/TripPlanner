import React, { useState, useCallback } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ChatPanel from "./components/ChatPanel";
import HomePage from "./pages/HomePage";
import PlanPage from "./pages/PlanPage";
import TripsListPage from "./pages/TripsListPage";
import TripDetailPage from "./pages/TripDetailPage";

const App: React.FC = () => {
  const [chatContext, setChatContext] = useState<string | null>(null);

  const handleSetContext = useCallback((ctx: string | null) => {
    setChatContext(ctx);
  }, []);

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/plan" element={<PlanPage />} />
        <Route path="/trips" element={<TripsListPage />} />
        <Route
          path="/trips/:id"
          element={<TripDetailPage onPlanContextChange={handleSetContext} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ChatPanel planContext={chatContext} />
    </Layout>
  );
};

export default App;
