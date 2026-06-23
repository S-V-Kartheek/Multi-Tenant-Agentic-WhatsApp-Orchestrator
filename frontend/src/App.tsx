// App.tsx — Route definitions (no auth guards for now)

import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { LandingPage } from './pages/LandingPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { InboxPage } from './pages/InboxPage';
import { EscalationPage } from './pages/EscalationPage';
import { BroadcastPage } from './pages/BroadcastPage';
import { TemplatesPage } from './pages/TemplatesPage';
import { SettingsPage } from './pages/SettingsPage';

export default function App() {
  return (
    <Routes>
      {/* Public landing page */}
      <Route path="/" element={<LandingPage />} />

      {/* Dashboard routes */}
      <Route element={<AppLayout />}>
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
