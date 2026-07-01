import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SettingsProvider } from './contexts/SettingsContext';
import { SessionProvider } from './contexts/SessionContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { Overview } from './pages/Overview';
import { Chat } from './pages/Chat';
import { Workflows } from './pages/Workflows';
import { Sessions } from './pages/Sessions';
import { Reports } from './pages/Reports';
import { Evidence } from './pages/Evidence';
import { Memory } from './pages/Memory';
import { Plugins } from './pages/Plugins';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SettingsProvider>
        <SessionProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<DashboardLayout />}>
                <Route index element={<Overview />} />
                <Route path="chat" element={<Chat />} />
                <Route path="workflows" element={<Workflows />} />
                <Route path="sessions" element={<Sessions />} />
                <Route path="reports" element={<Reports />} />
                <Route path="evidence" element={<Evidence />} />
                <Route path="memory" element={<Memory />} />
                <Route path="plugins" element={<Plugins />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </SessionProvider>
      </SettingsProvider>
    </QueryClientProvider>
  );
}

export default App;
