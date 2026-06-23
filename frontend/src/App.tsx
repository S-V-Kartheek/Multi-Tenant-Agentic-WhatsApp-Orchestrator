// App.tsx — Route definitions with Clerk auth guards

import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';
import { AppLayout } from './components/layout/AppLayout';
import { LandingPage } from './pages/LandingPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { InboxPage } from './pages/InboxPage';
import { EscalationPage } from './pages/EscalationPage';
import { BroadcastPage } from './pages/BroadcastPage';
import { TemplatesPage } from './pages/TemplatesPage';
import { SettingsPage } from './pages/SettingsPage';

// Protects any route — redirects to "/" if not signed in
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isSignedIn, isLoaded } = useAuth();
  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-[#030712] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 animate-pulse" />
          <p className="text-slate-500 text-sm">Loading...</p>
        </div>
      </div>
    );
  }
  if (!isSignedIn) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      {/* Public landing page */}
      <Route path="/" element={<LandingPage />} />

      {/* Protected dashboard routes */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<AnalyticsPage />} />
        <Route path="inbox" element={<InboxPage />} />
        <Route path="escalation" element={<EscalationPage />} />
        <Route path="broadcast" element={<BroadcastPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}
