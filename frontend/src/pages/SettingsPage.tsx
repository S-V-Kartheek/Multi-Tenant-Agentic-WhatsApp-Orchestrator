// pages/SettingsPage.tsx — App configuration overview

import { useApp } from '../context/AppContext';
import { Header } from '../components/layout/Header';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export function SettingsPage() {
  const { activeTenant, connectionState, tenants } = useApp();

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <Header title="Settings" subtitle="Environment & tenant configuration" />

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-lg space-y-6">
          <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Connection</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">API base URL</dt>
                <dd className="text-white font-mono text-xs">{API_BASE}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Live stream (SSE)</dt>
                <dd className="text-white capitalize">{connectionState}</dd>
              </div>
            </dl>
          </section>

          <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Active tenant</h3>
            {activeTenant ? (
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500 flex-shrink-0">Name</dt>
                  <dd className="text-white text-right">{activeTenant.name}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500 flex-shrink-0">Slug</dt>
                  <dd className="text-white font-mono text-xs">{activeTenant.slug}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500 flex-shrink-0">Phone number ID</dt>
                  <dd className="text-white font-mono text-xs truncate max-w-[180px]">
                    {activeTenant.phone_number_id}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500 flex-shrink-0">Media assets</dt>
                  <dd className="text-white">
                    {Object.keys(activeTenant.media_library).length}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="text-gray-500 text-sm">No tenant selected.</p>
            )}
          </section>

          <section className="bg-surface-card border border-surface-border rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4">All tenants ({tenants.length})</h3>
            <ul className="space-y-2">
              {tenants.map((t) => (
                <li
                  key={t.id}
                  className="flex items-center gap-3 p-2 rounded-lg bg-surface-elevated"
                >
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white"
                    style={{ backgroundColor: t.brand_color }}
                  >
                    {t.name.charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-white truncate">{t.name}</p>
                    <p className="text-[10px] text-gray-500">{t.slug}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
