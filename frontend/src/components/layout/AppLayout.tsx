// components/layout/AppLayout.tsx — Shared shell with sidebar + routed content

import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function AppLayout() {
  return (
    <div className="h-screen w-screen flex overflow-hidden bg-surface">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
