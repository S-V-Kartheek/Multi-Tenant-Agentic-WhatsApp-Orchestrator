// components/dashboard/StatusBadge.tsx — Session status pill component

import type { SessionStatus } from '../../types';

const STATUS_CONFIG: Record<
  SessionStatus,
  { label: string; color: string; dot: string }
> = {
  WAITING_FOR_BOT: {
    label: 'Waiting',
    color: 'text-status-waiting bg-status-waiting/10',
    dot: 'bg-status-waiting',
  },
  AGENT_RESPONDING: {
    label: 'Typing...',
    color: 'text-status-typing bg-status-typing/10',
    dot: 'bg-status-typing animate-pulse',
  },
  RESOLVED: {
    label: 'Resolved',
    color: 'text-status-resolved bg-status-resolved/10',
    dot: 'bg-status-resolved',
  },
  NEEDS_HUMAN: {
    label: 'Needs Human',
    color: 'text-status-human bg-status-human/10',
    dot: 'bg-status-human animate-pulse',
  },
  AGENT_HANDOFF: {
    label: 'Handoff',
    color: 'text-purple-400 bg-purple-400/10',
    dot: 'bg-purple-400',
  },
};

interface Props {
  status: SessionStatus;
  size?: 'xs' | 'sm' | 'md';
}

export function StatusBadge({ status, size = 'sm' }: Props) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.WAITING_FOR_BOT;

  const textSize = size === 'xs' ? 'text-[9px]' : size === 'sm' ? 'text-[10px]' : 'text-xs';
  const dotSize = size === 'xs' ? 'w-1 h-1' : 'w-1.5 h-1.5';
  const padding = size === 'xs' ? 'px-1.5 py-0.5' : 'px-2 py-0.5';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${textSize} ${padding} ${config.color}`}
    >
      <span className={`${dotSize} rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
}
