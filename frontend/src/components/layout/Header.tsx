// components/layout/Header.tsx — Top header bar with real SSE connection state

import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const STATE_MAP = {
  connected: { color: 'bg-status-resolved', label: 'Live', Icon: Wifi },
  connecting: { color: 'bg-yellow-400', label: 'Connecting', Icon: Loader2 },
  disconnected: { color: 'bg-gray-500', label: 'Offline', Icon: WifiOff },
  error: { color: 'bg-status-human', label: 'Reconnecting', Icon: WifiOff },
} as const;

interface Props {
  title?: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: Props) {
  const { activeTenant, sessions, connectionState } = useApp();
  const state = STATE_MAP[connectionState];
  const Icon = state.Icon;

  return (
    <div className="h-14 flex-shrink-0 px-4 flex items-center justify-between border-b border-surface-border bg-surface-card">
      <div className="flex items-center gap-3 min-w-0">
        {activeTenant ? (
          <>
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
              style={{ backgroundColor: activeTenant.brand_color }}
            >
              {activeTenant.name.charAt(0)}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-white leading-tight truncate">
                {title || activeTenant.name}
              </p>
              <p className="text-[10px] text-gray-500 truncate">
                {subtitle ??
                  `${sessions.length} conversation${sessions.length !== 1 ? 's' : ''}`}
              </p>
            </div>
          </>
        ) : (
          <p className="text-sm text-gray-500">{title || 'No tenant selected'}</p>
        )}
      </div>

      <div className="flex items-center gap-1.5 flex-shrink-0">
        <div
          className={`w-1.5 h-1.5 rounded-full ${state.color} ${connectionState === 'connected' ? 'animate-pulse' : ''}`}
        />
        <Icon
          size={10}
          className={`text-gray-500 ${connectionState === 'connecting' ? 'animate-spin' : ''}`}
        />
        <span className="text-[10px] text-gray-500">{state.label}</span>
      </div>
    </div>
  );
}
