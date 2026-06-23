// pages/EscalationPage.tsx — NEEDS_HUMAN + AGENT_HANDOFF queue with sentiment

import { AlertTriangle } from 'lucide-react';
import { Header } from '../components/layout/Header';
import { ChatList } from '../components/dashboard/ChatList';
import { ChatThread } from '../components/dashboard/ChatThread';
import { useApp } from '../context/AppContext';

export function EscalationPage() {
  const { selectedSession, sessions } = useApp();
  const queueCount = sessions.filter(
    (s) => s.status === 'NEEDS_HUMAN' || s.status === 'AGENT_HANDOFF',
  ).length;

  return (
    <div className="flex flex-1 overflow-hidden">
      <div
        className={`
          w-full md:w-72 lg:w-80 flex-shrink-0 border-r border-surface-border flex flex-col
          ${selectedSession ? 'hidden md:flex' : 'flex'}
        `}
      >
        <Header
          title="Escalation Queue"
          subtitle={`${queueCount} session${queueCount !== 1 ? 's' : ''} need attention`}
        />
        <ChatList defaultStatusFilter="NEEDS_HUMAN" escalationMode />
      </div>

      <div
        className={`
          flex-1 flex flex-col overflow-hidden min-w-0
          ${!selectedSession ? 'hidden md:flex' : 'flex'}
        `}
      >
        {selectedSession ? (
          <ChatThread session={selectedSession} />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <div className="w-20 h-20 rounded-2xl bg-status-human/10 flex items-center justify-center mb-4 glow-red">
              <AlertTriangle size={32} className="text-status-human" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Escalation queue</h2>
            <p className="text-gray-500 text-sm max-w-sm">
              Sessions flagged by sentiment analysis or manually escalated appear here. Take over and
              reply directly to the customer.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
