// components/dashboard/ChatThread.tsx — Chat view with agent actions + run trace

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Phone,
  AlertCircle,
  CheckCircle,
  UserPlus,
  RotateCcw,
  Send,
  GitBranch,
  ArrowLeft,
} from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { StatusBadge } from './StatusBadge';
import { RunTraceViewer } from '../traces/RunTraceViewer';
import { messagesApi, sessionsApi } from '../../api/client';
import { useApp } from '../../context/AppContext';
import type { ChatSession, Message, SessionStatus } from '../../types';

interface Props {
  session: ChatSession;
}

export function ChatThread({ session }: Props) {
  const { sseTick, sseTickSessionId, setSelectedSession, refreshSessions } = useApp();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [currentStatus, setCurrentStatus] = useState(session.status);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [showTrace, setShowTrace] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const loadMessages = useCallback(async () => {
    try {
      const res = await messagesApi.getBySession(session.id, { limit: 50 });
      setMessages(res.data);
      setHasMore(res.data.length >= 50);
    } catch {
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }, [session.id]);

  useEffect(() => {
    setLoading(true);
    setCurrentStatus(session.status);
    setShowTrace(false);
    loadMessages();
  }, [session.id, session.status, loadMessages]);

  useEffect(() => {
    if (sseTickSessionId === session.id) {
      loadMessages();
    }
  }, [sseTick, sseTickSessionId, session.id, loadMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const loadOlder = async () => {
    if (!hasMore || loadingMore || messages.length === 0) return;
    setLoadingMore(true);
    try {
      const res = await messagesApi.getBySession(session.id, {
        limit: 30,
        before_id: messages[0].id,
      });
      if (res.data.length === 0) setHasMore(false);
      else setMessages((prev) => [...res.data, ...prev]);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleScroll = () => {
    const el = scrollRef.current;
    if (el && el.scrollTop < 80) loadOlder();
  };

  const updateStatus = async (status: SessionStatus) => {
    setActionLoading(true);
    try {
      await sessionsApi.updateStatus(session.id, status);
      setCurrentStatus(status);
      refreshSessions();
    } finally {
      setActionLoading(false);
    }
  };

  const handleReply = async () => {
    if (!replyText.trim() || sending) return;
    setSending(true);
    try {
      await sessionsApi.sendReply(session.id, replyText.trim());
      setReplyText('');
      setCurrentStatus('AGENT_HANDOFF');
      await loadMessages();
      refreshSessions();
    } finally {
      setSending(false);
    }
  };

  const isNeedsHuman = currentStatus === 'NEEDS_HUMAN';
  const canReply =
    currentStatus === 'NEEDS_HUMAN' ||
    currentStatus === 'AGENT_HANDOFF' ||
    currentStatus === 'AGENT_RESPONDING';

  return (
    <div
      className={`flex flex-col h-full min-h-0 ${isNeedsHuman ? 'ring-1 ring-inset ring-status-human/30' : ''}`}
    >
      <div
        className={`
        h-14 flex-shrink-0 px-3 md:px-4 flex items-center justify-between border-b gap-2
        ${isNeedsHuman ? 'border-status-human/30 bg-status-human/5' : 'border-surface-border bg-surface-card'}
      `}
      >
        <div className="flex items-center gap-2 min-w-0">
          <button
            onClick={() => setSelectedSession(null)}
            className="md:hidden p-1 text-gray-400 hover:text-white"
          >
            <ArrowLeft size={16} />
          </button>
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
              isNeedsHuman ? 'bg-status-human/20 text-status-human' : 'bg-surface-elevated text-gray-300'
            }`}
          >
            <Phone size={14} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">{session.customer_phone}</p>
            <p className="text-[10px] text-gray-500">
              {session.message_count} messages · {new Date(session.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          {isNeedsHuman && (
            <div className="hidden sm:flex items-center gap-1 px-2 py-1 rounded-lg bg-status-human/10 border border-status-human/20">
              <AlertCircle size={12} className="text-status-human" />
              <span className="text-xs text-status-human font-medium">Human Required</span>
            </div>
          )}
          <StatusBadge status={currentStatus} size="sm" />
        </div>
      </div>

      {/* Agent action bar */}
      <div className="flex-shrink-0 px-3 py-2 border-b border-surface-border bg-surface-card/80 flex flex-wrap gap-1.5">
        <ActionButton
          icon={<CheckCircle size={12} />}
          label="Resolve"
          disabled={actionLoading || currentStatus === 'RESOLVED'}
          onClick={() => updateStatus('RESOLVED')}
        />
        <ActionButton
          icon={<AlertCircle size={12} />}
          label="Escalate"
          disabled={actionLoading || currentStatus === 'NEEDS_HUMAN'}
          onClick={() => updateStatus('NEEDS_HUMAN')}
        />
        <ActionButton
          icon={<UserPlus size={12} />}
          label="Take over"
          disabled={actionLoading || currentStatus === 'AGENT_HANDOFF'}
          onClick={() => updateStatus('AGENT_HANDOFF')}
        />
        <ActionButton
          icon={<RotateCcw size={12} />}
          label="Reopen"
          disabled={actionLoading}
          onClick={() => updateStatus('WAITING_FOR_BOT')}
        />
        <ActionButton
          icon={<GitBranch size={12} />}
          label={showTrace ? 'Hide trace' : 'Run trace'}
          onClick={() => setShowTrace((v) => !v)}
        />
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-0.5 min-h-0"
        style={{ background: 'linear-gradient(180deg, #0A0F1E 0%, #0D1424 100%)' }}
      >
        {loadingMore && (
          <div className="flex justify-center py-2">
            <div className="w-4 h-4 rounded-full border-2 border-brand-primary border-t-transparent animate-spin" />
          </div>
        )}
        {!loadingMore && hasMore && messages.length > 0 && (
          <button
            onClick={loadOlder}
            className="w-full text-center text-[10px] text-gray-500 hover:text-brand-glow py-2"
          >
            Load older messages
          </button>
        )}

        {loading && (
          <div className="flex items-center justify-center h-32">
            <div className="w-6 h-6 rounded-full border-2 border-brand-primary border-t-transparent animate-spin" />
          </div>
        )}

        {!loading && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-40 text-center">
            <p className="text-sm text-gray-500">No messages yet</p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <MessageBubble message={message} />
            </motion.div>
          ))}
        </AnimatePresence>

        <div ref={bottomRef} />
      </div>

      {currentStatus === 'AGENT_RESPONDING' && (
        <div className="h-8 flex-shrink-0 flex items-center px-4 bg-surface-card border-t border-surface-border">
          <div className="flex items-center gap-2">
            <div className="flex gap-0.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse-dot typing-dot"
                />
              ))}
            </div>
            <span className="text-xs text-gray-500">Bot is typing...</span>
          </div>
        </div>
      )}

      {canReply && (
        <div className="flex-shrink-0 p-3 border-t border-surface-border bg-surface-card flex gap-2">
          <input
            type="text"
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleReply()}
            placeholder="Type a manual reply to send via WhatsApp..."
            className="flex-1 bg-surface-elevated border border-surface-border rounded-xl px-3 py-2 text-sm text-white placeholder-gray-500 outline-none focus:border-brand-primary/50"
          />
          <button
            onClick={handleReply}
            disabled={!replyText.trim() || sending}
            className="px-4 rounded-xl bg-brand-primary text-white disabled:opacity-40 hover:opacity-90 transition-opacity flex items-center gap-1.5 text-sm font-medium"
          >
            {sending ? (
              <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
            ) : (
              <>
                <Send size={14} />
                Send
              </>
            )}
          </button>
        </div>
      )}

      <AnimatePresence>
        {showTrace && <RunTraceViewer sessionId={session.id} onClose={() => setShowTrace(false)} />}
      </AnimatePresence>
    </div>
  );
}

function ActionButton({
  icon,
  label,
  onClick,
  disabled,
}: {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium text-gray-400 hover:text-white bg-surface-elevated border border-surface-border hover:border-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
    >
      {icon}
      {label}
    </button>
  );
}
