import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/common/ProtectedRoute";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { AppLayout } from "@/components/layout";
import Dashboard from "@/pages/Dashboard";
import Cards from "@/pages/Cards";
import CardDetail from "@/pages/CardDetail";
import Briefings from "@/pages/Briefings";
import BriefingDetail from "@/pages/BriefingDetail";
import Competitors from "@/pages/Competitors";
import CompetitorDetail from "@/pages/CompetitorDetail";
import AugmentProfile from "@/pages/AugmentProfile";
import Feeds from "@/pages/Feeds";
import Settings from "@/pages/Settings";
import Login from "@/pages/Login";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ErrorBoundary>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<Dashboard />} />
                <Route path="cards" element={<Cards />} />
                <Route path="cards/:id" element={<CardDetail />} />
                <Route path="briefings" element={<Briefings />} />
                <Route path="briefings/:id" element={<BriefingDetail />} />
                <Route path="competitors" element={<Competitors />} />
                <Route path="competitors/:id" element={<CompetitorDetail />} />
                <Route path="augment-profile" element={<AugmentProfile />} />
                <Route path="feeds" element={<Feeds />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Route>
          </Routes>
          </ErrorBoundary>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
