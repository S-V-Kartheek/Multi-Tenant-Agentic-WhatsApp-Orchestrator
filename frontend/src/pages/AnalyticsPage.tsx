// pages/AnalyticsPage.tsx — Analytics Dashboard with KPIs + recharts

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  MessageSquare,
  Users,
  Clock,
  TrendingUp,
  AlertCircle,
  Radio,
  CheckCircle,
  Zap,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  CartesianGrid,
} from 'recharts';
import { metricsApi } from '../api/client';
import { useApp } from '../context/AppContext';
import { Header } from '../components/layout/Header';
import type { TenantMetrics } from '../types';

const STATUS_COLORS: Record<string, string> = {
  RESOLVED: '#10B981',
  WAITING_FOR_BOT: '#F59E0B',
  AGENT_RESPONDING: '#3B82F6',
  NEEDS_HUMAN: '#EF4444',
  AGENT_HANDOFF: '#8B5CF6',
};

function KPICard({
  label,
  value,
  icon,
  color,
  sub,
}: {
  label: string;
  value: React.ReactNode;
  icon: React.ReactNode;
  color: string;
  sub?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-card rounded-2xl border border-surface-border p-5 flex flex-col gap-3"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">{label}</span>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>{icon}</div>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-[11px] text-gray-500">{sub}</p>}
    </motion.div>
  );
}

function SentimentGauge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-gray-500">—</span>;
  const pct = Math.round(score * 100);
  const color =
    score >= 0.7 ? 'text-status-resolved' : score >= 0.4 ? 'text-yellow-400' : 'text-status-human';
  return <span className={`text-2xl font-bold ${color}`}>{pct}%</span>;
}

export function AnalyticsPage() {
  const { activeTenant } = useApp();
  const [metrics, setMetrics] = useState<TenantMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!activeTenant) return;
    setLoading(true);
    metricsApi
      .getTenantMetrics(activeTenant.id)
      .then((res) => setMetrics(res.data))
      .catch(() => setMetrics(null))
      .finally(() => setLoading(false));
  }, [activeTenant]);

  const dailyData =
    metrics?.daily_volume.map((d) => ({
      ...d,
      date: new Date(d.date).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
    })) ?? [];

  const statusPieData = metrics
    ? Object.entries(metrics.status_distribution).map(([name, value]) => ({
        name: name.replace(/_/g, ' '),
        value,
        color: STATUS_COLORS[name] || '#6B7280',
      }))
    : [];

  const hourlyData = metrics
    ? Object.values(
        metrics.hourly_volume.reduce<Record<string, { hour: string; inbound: number; outbound: number }>>(
          (acc, row) => {
            const key = row.hour.slice(0, 13);
            if (!acc[key]) acc[key] = { hour: key, inbound: 0, outbound: 0 };
            if (row.direction === 'inbound') acc[key].inbound += row.count;
            else acc[key].outbound += row.count;
            return acc;
          },
          {},
        ),
      ).slice(-12)
    : [];

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <Header title="Analytics" />
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 bg-surface">
        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 rounded-full border-2 border-brand-primary border-t-transparent animate-spin" />
          </div>
        )}

        {!loading && !metrics && (
          <p className="text-center text-gray-500 py-24">Unable to load metrics. Is the backend running?</p>
        )}

        {!loading && metrics && (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
              <KPICard
                label="Total Sessions"
                value={metrics.total_sessions}
                icon={<Users size={16} className="text-brand-glow" />}
                color="bg-brand-primary/10"
                sub={`${metrics.active_sessions} active`}
              />
              <KPICard
                label="Resolution Rate"
                value={`${(metrics.resolution_rate * 100).toFixed(0)}%`}
                icon={<CheckCircle size={16} className="text-status-resolved" />}
                color="bg-status-resolved/10"
                sub={`${metrics.resolved_sessions} resolved`}
              />
              <KPICard
                label="Total Messages"
                value={metrics.total_messages}
                icon={<MessageSquare size={16} className="text-blue-400" />}
                color="bg-blue-500/10"
                sub={`${metrics.inbound_messages} in / ${metrics.outbound_messages} out`}
              />
              <KPICard
                label="Needs Human"
                value={metrics.needs_human_sessions}
                icon={<AlertCircle size={16} className="text-status-human" />}
                color="bg-status-human/10"
                sub="Escalation queue"
              />
              <KPICard
                label="Avg Response Time"
                value={
                  metrics.avg_resolution_time_sec
                    ? `${metrics.avg_resolution_time_sec.toFixed(1)}s`
                    : '—'
                }
                icon={<Clock size={16} className="text-yellow-400" />}
                color="bg-yellow-500/10"
                sub="Session resolution"
              />
              <KPICard
                label="Customer Sentiment"
                value={<SentimentGauge score={metrics.avg_sentiment} />}
                icon={<TrendingUp size={16} className="text-green-400" />}
                color="bg-green-500/10"
                sub="Average across sessions"
              />
              <KPICard
                label="Broadcasts Sent"
                value={metrics.broadcasts_sent}
                icon={<Radio size={16} className="text-purple-400" />}
                color="bg-purple-500/10"
                sub="Template campaigns"
              />
              <KPICard
                label="Recent Runs"
                value={metrics.recent_runs.length}
                icon={<Zap size={16} className="text-brand-glow" />}
                color="bg-brand-primary/10"
                sub="LangGraph executions"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
              <div className="lg:col-span-2 bg-surface-card rounded-2xl border border-surface-border p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <BarChart3 size={14} className="text-brand-primary" />
                  Message Volume (14 days)
                </h3>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={dailyData}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: '#6B7280', fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis tick={{ fill: '#6B7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: '#111827',
                        border: '1px solid #1F2937',
                        borderRadius: '12px',
                        fontSize: 12,
                      }}
                      labelStyle={{ color: '#F9FAFB' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="count"
                      stroke="#6366F1"
                      fill="url(#colorCount)"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-surface-card rounded-2xl border border-surface-border p-5">
                <h3 className="text-sm font-semibold text-white mb-4">Status Distribution</h3>
                {statusPieData.length > 0 ? (
                  <>
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie
                          data={statusPieData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          innerRadius={45}
                          outerRadius={70}
                          paddingAngle={3}
                        >
                          {statusPieData.map((entry, i) => (
                            <Cell key={i} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            background: '#111827',
                            border: '1px solid #1F2937',
                            borderRadius: '12px',
                            fontSize: 12,
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-2 space-y-1">
                      {statusPieData.map((entry) => (
                        <div key={entry.name} className="flex items-center gap-2 text-xs">
                          <span
                            className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{ backgroundColor: entry.color }}
                          />
                          <span className="text-gray-400 flex-1">{entry.name}</span>
                          <span className="text-white font-medium">{entry.value}</span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-gray-500 text-sm text-center py-12">No session data yet</p>
                )}
              </div>
            </div>

            {hourlyData.length > 0 && (
              <div className="bg-surface-card rounded-2xl border border-surface-border p-5">
                <h3 className="text-sm font-semibold text-white mb-4">Hourly Message Volume</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={hourlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                    <XAxis
                      dataKey="hour"
                      tick={{ fill: '#6B7280', fontSize: 10 }}
                      tickFormatter={(v: string) =>
                        new Date(v).toLocaleTimeString([], { hour: '2-digit' })
                      }
                    />
                    <YAxis tick={{ fill: '#6B7280', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: '#111827',
                        border: '1px solid #1F2937',
                        borderRadius: '12px',
                        fontSize: 12,
                      }}
                    />
                    <Bar dataKey="inbound" fill="#3B82F6" name="Inbound" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="outbound" fill="#6366F1" name="Outbound" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {metrics.recent_runs.length > 0 && (
              <div className="bg-surface-card rounded-2xl border border-surface-border p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Zap size={14} className="text-brand-primary" />
                  Recent Agent Runs
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-gray-500 border-b border-surface-border">
                        <th className="text-left py-2 pr-4">Phone</th>
                        <th className="text-left py-2 pr-4">Status</th>
                        <th className="text-left py-2 pr-4">Tool</th>
                        <th className="text-left py-2 pr-4">Sentiment</th>
                        <th className="text-right py-2">Duration</th>
                      </tr>
                    </thead>
                    <tbody>
                      {metrics.recent_runs.map((run) => (
                        <tr key={run.id} className="border-b border-surface-border/50 text-gray-300">
                          <td className="py-2 pr-4 font-mono">{run.customer_phone.slice(-6)}</td>
                          <td className="py-2 pr-4">
                            <span
                              className={
                                run.escalated ? 'text-status-human' : 'text-status-resolved'
                              }
                            >
                              {run.status}
                            </span>
                          </td>
                          <td className="py-2 pr-4 text-brand-glow">{run.tool_chosen || '—'}</td>
                          <td className="py-2 pr-4">
                            {run.sentiment_score != null
                              ? `${Math.round(run.sentiment_score * 100)}%`
                              : '—'}
                          </td>
                          <td className="py-2 text-right text-gray-500">
                            {run.duration_ms != null ? `${run.duration_ms}ms` : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
