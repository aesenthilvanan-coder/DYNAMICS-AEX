import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dynamics from "./pages/Dynamics";
import AppShell from "./components/layout/AppShell";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30000 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <AppShell>
                <Dynamics />
              </AppShell>
            }
          />
          <Route
            path="/dynamics"
            element={
              <AppShell>
                <Dynamics />
              </AppShell>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
