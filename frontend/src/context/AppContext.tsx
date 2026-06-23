// context/AppContext.tsx — Global state provider (tenants, sessions, SSE, connection state)

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import { useSSE, type SSEConnectionState } from '../hooks/useSSE';
import { tenantsApi, sessionsApi } from '../api/client';
import type { Tenant, ChatSession, SSEEvent } from '../types';

interface SessionQuery {
  status?: string;
  search?: string;
  limit?: number;
}

interface AppState {
  tenants: Tenant[];
  activeTenant: Tenant | null;
  setActiveTenant: (t: Tenant) => void;
  sessions: ChatSession[];
  setSessions: React.Dispatch<React.SetStateAction<ChatSession[]>>;
  selectedSession: ChatSession | null;
  setSelectedSession: (s: ChatSession | null) => void;
  connectionState: SSEConnectionState;
  refreshSessions: (params?: SessionQuery) => Promise<void>;
  sseTick: number;
  sseTickSessionId: string | null;
}

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [activeTenant, setActiveTenant] = useState<Tenant | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [sseTick, setSseTick] = useState(0);
  const [sseTickSessionId, setSseTickSessionId] = useState<string | null>(null);

  const refreshSessions = useCallback(
    async (params?: SessionQuery) => {
      if (!activeTenant) return;
      try {
        const res = await sessionsApi.getByTenant(activeTenant.id, {
          limit: params?.limit ?? 50,
          status: params?.status && params.status !== 'ALL' ? params.status : undefined,
          search: params?.search?.trim() || undefined,
        });
        setSessions(res.data);
      } catch {
        /* keep existing sessions */
      }
    },
    [activeTenant],
  );

  useEffect(() => {
    tenantsApi
      .getAll()
      .then((res) => {
        setTenants(res.data);
        if (res.data.length > 0) setActiveTenant(res.data[0]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setSelectedSession(null);
    refreshSessions();
  }, [activeTenant, refreshSessions]);

  // Keep selected session in sync when list updates (status, counts)
  useEffect(() => {
    if (!selectedSession) return;
    const updated = sessions.find((s) => s.id === selectedSession.id);
    if (
      updated &&
      (updated.status !== selectedSession.status ||
        updated.message_count !== selectedSession.message_count)
    ) {
      setSelectedSession(updated);
    }
  }, [sessions, selectedSession]);

  const handleSSEEvent = useCallback(
    (event: SSEEvent) => {
      if (event.type === 'session_updated' && event.data) {
        const { session_id, status } = event.data as { session_id: string; status: string };
        setSessions((prev) =>
          prev
            .map((s) =>
              s.id === session_id
                ? { ...s, status: status as ChatSession['status'], last_activity: new Date().toISOString() }
                : s,
            )
            .sort((a, b) => new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime()),
        );
        setSseTickSessionId(session_id);
        setSseTick((t) => t + 1);
      } else if (event.type === 'new_message' && event.data) {
        const { session_id } = event.data as { session_id: string };
        setSessions((prev) =>
          prev
            .map((s) =>
              s.id === session_id
                ? { ...s, message_count: s.message_count + 1, last_activity: new Date().toISOString() }
                : s,
            )
            .sort((a, b) => new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime()),
        );
        setSseTickSessionId(session_id);
        setSseTick((t) => t + 1);
      } else if (event.type === 'typing_on' && event.data) {
        const { session_id } = event.data as { session_id: string };
        setSessions((prev) =>
          prev.map((s) =>
            s.id === session_id ? { ...s, status: 'AGENT_RESPONDING' as ChatSession['status'] } : s,
          ),
        );
        setSseTickSessionId(session_id);
        setSseTick((t) => t + 1);
      } else if (event.type === 'campaign_created') {
        refreshSessions();
      }
    },
    [refreshSessions],
  );

  const { connectionState } = useSSE(activeTenant?.id ?? null, handleSSEEvent);

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-surface">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-brand-primary border-t-transparent animate-spin" />
          <p className="text-gray-400 text-sm">Connecting to agent...</p>
        </div>
      </div>
    );
  }

  return (
    <AppContext.Provider
      value={{
        tenants,
        activeTenant,
        setActiveTenant,
        sessions,
        setSessions,
        selectedSession,
        setSelectedSession,
        connectionState,
        refreshSessions,
        sseTick,
        sseTickSessionId,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
