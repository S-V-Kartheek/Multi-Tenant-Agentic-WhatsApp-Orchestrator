// App.tsx — Route definitions

import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { InboxPage } from './pages/InboxPage';
import { EscalationPage } from './pages/EscalationPage';
import { BroadcastPage } from './pages/BroadcastPage';
import { TemplatesPage } from './pages/TemplatesPage';
import { SettingsPage } from './pages/SettingsPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
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
