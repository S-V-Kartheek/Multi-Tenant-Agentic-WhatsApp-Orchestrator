// types/index.ts — Shared TypeScript interfaces mirroring backend Pydantic models

export type SessionStatus =
  | 'WAITING_FOR_BOT'
  | 'AGENT_RESPONDING'
  | 'RESOLVED'
  | 'NEEDS_HUMAN'
  | 'AGENT_HANDOFF';

export type MessageDirection = 'inbound' | 'outbound';

export type MessageType =
  | 'text'
  | 'image'
  | 'audio'
  | 'video'
  | 'document'
  | 'sticker'
  | 'location'
  | 'contacts'
  | 'interactive'
  | 'template'
  | 'typing_indicator'
  | 'status_update'
  | 'system';

export interface Tenant {
  id: string;
  slug: string;
  name: string;
  phone_number_id: string;
  system_prompt: string;
  media_library: Record<string, string>;
  brand_color: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  tenant_id: string;
  customer_phone: string;
  status: SessionStatus;
  message_count: number;
  last_activity: string;
  created_at: string;
  sentiment_score?: number | null;
  last_run_id?: string | null;
}

export interface Message {
  id: string;
  session_id: string;
  direction: MessageDirection;
  sender: string;
  message_type: MessageType;
  text_content: string | null;
  media_url: string | null;
  media_mime_type: string | null;
  media_filename: string | null;
  delivery_status: string | null;
  agent_state_snapshot: Record<string, unknown>;
  timestamp: string;
}

export interface SSEEvent {
  type:
    | 'connected'
    | 'ping'
    | 'new_message'
    | 'session_updated'
    | 'typing_on'
    | 'campaign_created';
  data?: Record<string, unknown>;
  tenant_id?: string;
}

export interface BroadcastRequest {
  tenant_id: string;
  template_name: string;
  phone_numbers: string[];
  language_code?: string;
}

// ── Analytics ────────────────────────────────────────────────────────────────

export interface TenantMetrics {
  tenant_id: string;
  total_sessions: number;
  active_sessions: number;
  resolved_sessions: number;
  needs_human_sessions: number;
  resolution_rate: number;
  total_messages: number;
  inbound_messages: number;
  outbound_messages: number;
  broadcasts_sent: number;
  avg_resolution_time_sec: number | null;
  avg_sentiment: number | null;
  status_distribution: Record<string, number>;
  message_type_distribution: Record<string, number>;
  hourly_volume: Array<{ hour: string; direction: string; count: number }>;
  daily_volume: Array<{ date: string; count: number }>;
  recent_runs: AgentRunSummary[];
}

export interface AgentRunSummary {
  id: string;
  session_id: string;
  customer_phone: string;
  status: string;
  tool_chosen: string | null;
  response_type: string | null;
  sentiment_score: number | null;
  escalated: boolean;
  duration_ms: number | null;
  started_at: string;
}

// ── Agent Run Trace ──────────────────────────────────────────────────────────

export interface AgentRunStep {
  node: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  snapshot: Record<string, unknown>;
}

export interface AgentRun {
  id: string;
  tenant_id: string;
  session_id: string;
  customer_phone: string;
  inbound_text: string | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  steps: AgentRunStep[];
  tool_chosen: string | null;
  response_type: string | null;
  sentiment_score: number | null;
  escalated: boolean;
  error: string | null;
}

// ── Broadcast Templates & Campaigns ──────────────────────────────────────────

export interface BroadcastTemplate {
  name: string;
  label: string;
  category: string;
  language: string;
  description: string;
  body_preview: string;
}

export interface BroadcastCampaign {
  id: string;
  tenant_id: string;
  template_name: string;
  language_code: string;
  recipient_count: number;
  sent: number;
  failed: number;
  created_at: string;
}
