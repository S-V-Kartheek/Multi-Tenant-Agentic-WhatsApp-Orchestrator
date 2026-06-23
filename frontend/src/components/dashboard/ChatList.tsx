// components/dashboard/ChatList.tsx — Session list with server-side search + filter

import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, Search, ArrowLeft } from 'lucide-react';
import { StatusBadge } from './StatusBadge';
import { useApp } from '../../context/AppContext';
import { sessionsApi } from '../../api/client';
import type { SessionStatus } from '../../types';

const STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'ALL', label: 'All' },
  { value: 'WAITING_FOR_BOT', label: 'Waiting' },
  { value: 'AGENT_RESPONDING', label: 'Typing' },
  { value: 'RESOLVED', label: 'Resolved' },
  { value: 'NEEDS_HUMAN', label: 'Needs Human' },
  { value: 'AGENT_HANDOFF', label: 'Handoff' },
];

function formatTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  return d.toLocaleDateString();
}

function maskPhone(phone: string): string {
  if (phone.length < 7) return phone;
  return phone.slice(0, -4).replace(/\d/g, '*') + phone.slice(-4);
}

interface Props {
  defaultStatusFilter?: string;
  escalationMode?: boolean;
}

export function ChatList({ defaultStatusFilter = 'ALL', escalationMode = false }: Props) {
  const { sessions, selectedSession, setSelectedSession, refreshSessions } = useApp();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState(defaultStatusFilter);
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [previews, setPreviews] = useState<Record<string, string | null>>({});

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    if (escalationMode) return;
    refreshSessions({
      status: statusFilter !== 'ALL' ? statusFilter : undefined,
      search: debouncedSearch || undefined,
    });
  }, [statusFilter, debouncedSearch, escalationMode, refreshSessions]);

  const filtered = useMemo(() => {
    if (!escalationMode) return sessions;
    let list = sessions.filter(
      (s) => s.status === 'NEEDS_HUMAN' || s.status === 'AGENT_HANDOFF',
    );
    if (debouncedSearch.trim()) {
      const term = debouncedSearch.trim().toLowerCase();
      list = list.filter((s) => s.customer_phone.toLowerCase().includes(term));
    }
    if (statusFilter !== 'ALL' && statusFilter !== 'NEEDS_HUMAN') {
      list = list.filter((s) => s.status === statusFilter);
    }
    return list;
  }, [sessions, escalationMode, debouncedSearch, statusFilter]);

  useEffect(() => {
    filtered.slice(0, 20).forEach((s) => {
      if (previews[s.id] !== undefined) return;
      sessionsApi
        .getPreview(s.id)
        .then((res) => setPreviews((p) => ({ ...p, [s.id]: res.data.preview })))
        .catch(() => setPreviews((p) => ({ ...p, [s.id]: null })));
    });
  }, [filtered, previews]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {selectedSession && (
        <button
          onClick={() => setSelectedSession(null)}
          className="md:hidden flex items-center gap-2 px-4 py-2 text-xs text-brand-glow border-b border-surface-border"
        >
          <ArrowLeft size={14} />
          Back to list
        </button>
      )}

      <div className="p-3 space-y-2 border-b border-surface-border/50">
        <div className="flex items-center gap-2 bg-surface-elevated rounded-xl px-3 py-2">
          <Search size={13} className="text-gray-500 flex-shrink-0" />
          <input
            type="text"
            placeholder="Search phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 bg-transparent text-xs text-white placeholder-gray-500 outline-none"
          />
        </div>
        {!escalationMode && (
          <div className="flex gap-1 overflow-x-auto no-scrollbar">
            {STATUS_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setStatusFilter(opt.value)}
                className={`px-2 py-1 rounded-lg text-[10px] font-medium whitespace-nowrap transition-colors ${
                  statusFilter === opt.value
                    ? 'bg-brand-primary/15 text-brand-glow border border-brand-primary/30'
                    : 'text-gray-500 hover:text-gray-300 border border-transparent'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-center px-4">
            <Phone size={24} className="text-gray-600 mb-2" />
            <p className="text-xs text-gray-500">
              {escalationMode ? 'No escalated sessions' : 'No conversations found'}
            </p>
          </div>
        )}

        <AnimatePresence>
          {filtered.map((session) => {
            const isSelected = selectedSession?.id === session.id;
            const isNeedsHuman =
              session.status === 'NEEDS_HUMAN' || session.status === 'AGENT_HANDOFF';
            const preview = previews[session.id];

            return (
              <motion.button
                key={session.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.15 }}
                onClick={() => setSelectedSession(session)}
                className={`
                  w-full px-4 py-3 flex items-center gap-3 text-left transition-all duration-200
                  border-b border-surface-border/50 hover:bg-surface-elevated
                  ${isSelected ? 'bg-surface-elevated border-l-2 border-l-brand-primary' : ''}
                  ${isNeedsHuman ? 'glow-red' : ''}
                `}
              >
                <div
                  className={`
                  w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold
                  ${isNeedsHuman
                    ? 'bg-status-human/20 text-status-human ring-1 ring-status-human/50'
                    : 'bg-surface-elevated text-gray-300'
                  }
                `}
                >
                  {session.customer_phone.slice(-2)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-sm font-medium text-white truncate">
                      {maskPhone(session.customer_phone)}
                    </span>
                    <span className="text-[10px] text-gray-600 flex-shrink-0 ml-1">
                      {formatTime(session.last_activity)}
                    </span>
                  </div>
                  {preview && (
                    <p className="text-[10px] text-gray-500 truncate mb-1">{preview}</p>
                  )}
                  <div className="flex items-center justify-between">
                    <StatusBadge status={session.status as SessionStatus} size="xs" />
                    <span className="text-[10px] text-gray-600">{session.message_count} msgs</span>
                  </div>
                </div>
              </motion.button>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
