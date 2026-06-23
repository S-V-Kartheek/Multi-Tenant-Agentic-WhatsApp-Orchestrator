// api/client.ts — Axios API client with all endpoint surfaces

import axios from 'axios';
import type { BroadcastRequest, BroadcastCampaign, BroadcastTemplate, TenantMetrics, AgentRun, ChatSession, AgentRunSummary } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ── Tenant API ────────────────────────────────────────────────────────────────
export const tenantsApi = {
  getAll: () => apiClient.get<Tenant[]>('/api/tenants'),
  getById: (id: string) => apiClient.get(`/api/tenants/${id}`),
};

// ── Sessions API ──────────────────────────────────────────────────────────────
export const sessionsApi = {
  getByTenant: (tenantId: string, params?: { limit?: number; status?: string; search?: string }) =>
    apiClient.get<ChatSession[]>(`/api/sessions/${tenantId}`, { params }),
  getById: (sessionId: string) => apiClient.get<ChatSession>(`/api/session/${sessionId}`),
  updateStatus: (sessionId: string, status: string, agentId?: string) =>
    apiClient.patch(`/api/sessions/${sessionId}/status`, { status, agent_id: agentId }),
  sendReply: (sessionId: string, text: string, agentId?: string) =>
    apiClient.post(`/api/sessions/${sessionId}/reply`, { text, agent_id: agentId }),
  getPreview: (sessionId: string) =>
    apiClient.get<{ session_id: string; preview: string | null }>(`/api/sessions/${sessionId}/preview`),
};

// ── Messages API ──────────────────────────────────────────────────────────────
export const messagesApi = {
  getBySession: (sessionId: string, params?: { limit?: number; before_id?: string }) =>
    apiClient.get(`/api/messages/${sessionId}`, { params }),
};

// ── Broadcast API ─────────────────────────────────────────────────────────────
export const broadcastApi = {
  send: (payload: BroadcastRequest) =>
    apiClient.post<{ campaign_id: string; sent: number; failed: number }>('/api/broadcast', payload),
  getHistory: (tenantId: string, limit = 25) =>
    apiClient.get<BroadcastCampaign[]>(`/api/campaigns/${tenantId}`, { params: { limit } }),
};

// ── Templates API ─────────────────────────────────────────────────────────────
export const templatesApi = {
  getAll: () => apiClient.get<BroadcastTemplate[]>('/api/templates'),
};

// ── Metrics / Analytics API ──────────────────────────────────────────────────
export const metricsApi = {
  getTenantMetrics: (tenantId: string) =>
    apiClient.get<TenantMetrics>(`/api/metrics/${tenantId}`),
};

// ── Agent Runs API ───────────────────────────────────────────────────────────
export const runsApi = {
  getById: (runId: string) => apiClient.get<AgentRun>(`/api/runs/${runId}`),
  getBySession: (sessionId: string, limit = 20) =>
    apiClient.get<AgentRun[]>(`/api/runs/sessions/${sessionId}`, { params: { limit } }),
  getByTenant: (tenantId: string, limit = 10) =>
    apiClient.get<AgentRunSummary[]>(`/api/runs/tenants/${tenantId}`, { params: { limit } }),
};

// ── SSE URL helper ────────────────────────────────────────────────────────────
export const getSSEUrl = (tenantId: string) =>
  `${BASE_URL}/api/sse/${tenantId}`;

// Re-export the Tenant type so other files don't need to import from types
import type { Tenant } from '../types';
export type { Tenant };
