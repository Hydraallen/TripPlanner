import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import PlanPage from "./pages/PlanPage";
import TripsListPage from "./pages/TripsListPage";
import TripDetailPage from "./pages/TripDetailPage";

const App: React.FC = () => (
  <Layout>
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/plan" element={<PlanPage />} />
      <Route path="/trips" element={<TripsListPage />} />
      <Route path="/trips/:id" element={<TripDetailPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </Layout>
);

export default App;
