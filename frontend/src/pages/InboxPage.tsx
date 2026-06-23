// pages/InboxPage.tsx — Live chat monitor with session list + thread

import { MessageSquare } from 'lucide-react';
import { Header } from '../components/layout/Header';
import { ChatList } from '../components/dashboard/ChatList';
import { ChatThread } from '../components/dashboard/ChatThread';
import { useApp } from '../context/AppContext';

export function InboxPage() {
  const { selectedSession } = useApp();

  return (
    <div className="flex flex-1 overflow-hidden">
      <div
        className={`
          w-full md:w-72 lg:w-80 flex-shrink-0 border-r border-surface-border flex flex-col
          ${selectedSession ? 'hidden md:flex' : 'flex'}
        `}
      >
        <Header title="Inbox" />
        <ChatList />
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
          <EmptyState />
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center p-8 animate-fade-in">
      <div className="w-20 h-20 rounded-2xl bg-surface-elevated flex items-center justify-center mb-4 glow-indigo">
        <MessageSquare size={32} className="text-brand-primary" />
      </div>
      <h2 className="text-xl font-semibold text-white mb-2">Select a conversation</h2>
      <p className="text-gray-500 text-sm max-w-xs">
        Choose a customer from the list to view their thread, reply manually, or inspect agent runs.
      </p>
    </div>
  );
}
