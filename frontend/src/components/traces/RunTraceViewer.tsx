// components/traces/RunTraceViewer.tsx — Visual timeline of LangGraph state flow

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ChevronRight,
  Clock,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  Brain,
  Database,
  Send,
} from 'lucide-react';
import { runsApi } from '../../api/client';
import type { AgentRun } from '../../types';

interface Props {
  sessionId: string;
  onClose: () => void;
}

const NODE_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  acknowledge: {
    icon: <Zap size={14} />,
    color: 'text-yellow-400 bg-yellow-400/10',
    label: 'Acknowledge',
  },
  context_retriever: {
    icon: <Database size={14} />,
    color: 'text-blue-400 bg-blue-400/10',
    label: 'Context Retriever',
  },
  llm_reasoning: {
    icon: <Brain size={14} />,
    color: 'text-purple-400 bg-purple-400/10',
    label: 'LLM Reasoning',
  },
  dispatcher: {
    icon: <Send size={14} />,
    color: 'text-brand-glow bg-brand-primary/10',
    label: 'Dispatcher',
  },
  needs_human: {
    icon: <AlertTriangle size={14} />,
    color: 'text-status-human bg-status-human/10',
    label: 'Needs Human',
  },
};

const STATUS_ICON: Record<string, React.ReactNode> = {
  running: <Loader2 size={12} className="animate-spin text-blue-400" />,
  completed: <CheckCircle size={12} className="text-status-resolved" />,
  failed: <XCircle size={12} className="text-status-human" />,
  escalated: <AlertTriangle size={12} className="text-status-human" />,
};

function StepTimeline({ step, isLast }: { step: AgentRun['steps'][0]; isLast: boolean }) {
  const config = NODE_CONFIG[step.node] || {
    icon: <Zap size={14} />,
    color: 'text-gray-400 bg-gray-400/10',
    label: step.node,
  };
  const isError = step.status === 'failed';
  const isEscalated = step.status === 'escalated';
  const borderCol = isError || isEscalated ? 'border-status-human' : 'border-brand-primary';

  return (
    <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${config.color}`}>
          {config.icon}
        </div>
        {!isLast && <div className={`w-0.5 flex-1 min-h-[32px] border-l border-dashed ${borderCol}`} />}
      </div>

      <div className="flex-1 pb-4 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span className="text-sm font-medium text-white">{config.label}</span>
          {STATUS_ICON[step.status] || null}
          {step.duration_ms != null && (
            <span className="text-[10px] text-gray-500 flex items-center gap-0.5">
              <Clock size={9} />
              {step.duration_ms}ms
            </span>
          )}
        </div>

        {step.snapshot && Object.keys(step.snapshot).length > 0 && (
          <div className="bg-surface-elevated rounded-lg p-2.5 text-[11px] font-mono text-gray-400 space-y-0.5 overflow-x-auto">
            {Object.entries(step.snapshot).map(([key, val]) => (
              <div key={key} className="flex gap-2">
                <span className="text-brand-glow flex-shrink-0">{key}:</span>
                <span className="text-gray-300 truncate">
                  {typeof val === 'number' ? val.toFixed(2) : String(val).slice(0, 80)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function RunTraceViewer({ sessionId, onClose }: Props) {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    runsApi
      .getBySession(sessionId, 10)
      .then((res) => {
        setRuns(res.data);
        if (res.data.length > 0) setSelectedRun(res.data[0]);
      })
      .catch(() => setRuns([]))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const completedSteps =
    selectedRun?.steps.filter((s) => s.status !== 'running' || s.finished_at) ?? [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="border-t border-surface-border bg-surface-card flex-shrink-0"
    >
      <div className="px-4 py-2.5 flex items-center justify-between border-b border-surface-border/50">
        <div className="flex items-center gap-2 flex-wrap">
          <ChevronRight size={14} className="text-brand-primary" />
          <span className="text-xs font-semibold text-white">Agent Run Trace</span>
          {selectedRun && (
            <>
              <span
                className={`px-1.5 py-0.5 rounded-full text-[9px] font-medium ${
                  selectedRun.status === 'completed'
                    ? 'bg-status-resolved/10 text-status-resolved'
                    : selectedRun.status === 'escalated'
                      ? 'bg-status-human/10 text-status-human'
                      : 'bg-yellow-500/10 text-yellow-400'
                }`}
              >
                {selectedRun.status}
              </span>
              {selectedRun.duration_ms != null && (
                <span className="text-[10px] text-gray-500">{selectedRun.duration_ms}ms total</span>
              )}
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {runs.length > 1 && (
            <select
              value={selectedRun?.id || ''}
              onChange={(e) => setSelectedRun(runs.find((r) => r.id === e.target.value) || null)}
              className="bg-surface-elevated border border-surface-border rounded-lg px-2 py-1 text-xs text-gray-300 outline-none"
            >
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {new Date(r.started_at).toLocaleTimeString()}
                </option>
              ))}
            </select>
          )}
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xs">
            Close
          </button>
        </div>
      </div>

      <div className="p-4 overflow-y-auto max-h-[280px]">
        {loading && (
          <div className="flex justify-center py-6">
            <div className="w-5 h-5 rounded-full border-2 border-brand-primary border-t-transparent animate-spin" />
          </div>
        )}

        {!loading && runs.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-6">No agent runs for this conversation yet.</p>
        )}

        {!loading && selectedRun && (
          <>
            <div className="flex gap-3 mb-4">
              <div className="w-8 h-8 rounded-xl bg-surface-elevated flex items-center justify-center flex-shrink-0">
                <span className="text-[10px] font-bold text-gray-400">IN</span>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-0.5">Inbound message</p>
                <p className="text-sm text-gray-300 truncate max-w-md">
                  {selectedRun.inbound_text || '(media message)'}
                </p>
              </div>
            </div>

            <div className="bg-surface-elevated rounded-xl p-3 mb-4 flex flex-wrap items-center gap-4 text-xs">
              {selectedRun.tool_chosen && (
                <div className="flex items-center gap-1.5">
                  <span className="text-gray-500">Tool:</span>
                  <span className="text-brand-glow font-medium">{selectedRun.tool_chosen}</span>
                </div>
              )}
              {selectedRun.response_type && (
                <div className="flex items-center gap-1.5">
                  <span className="text-gray-500">Response:</span>
                  <span className="text-white font-medium">{selectedRun.response_type}</span>
                </div>
              )}
              {selectedRun.sentiment_score != null && (
                <div className="flex items-center gap-1.5">
                  <span className="text-gray-500">Sentiment:</span>
                  <span
                    className={`font-medium ${
                      selectedRun.sentiment_score >= 0.7
                        ? 'text-status-resolved'
                        : selectedRun.sentiment_score >= 0.4
                          ? 'text-yellow-400'
                          : 'text-status-human'
                    }`}
                  >
                    {Math.round(selectedRun.sentiment_score * 100)}%
                  </span>
                </div>
              )}
              {selectedRun.escalated && (
                <span className="text-status-human font-medium">Escalated to human</span>
              )}
            </div>

            {completedSteps.map((step, i) => (
              <StepTimeline
                key={`${step.node}-${step.started_at}-${i}`}
                step={step}
                isLast={i === completedSteps.length - 1}
              />
            ))}

            {selectedRun.error && (
              <p className="text-xs text-status-human mt-2 font-mono">{selectedRun.error}</p>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}
