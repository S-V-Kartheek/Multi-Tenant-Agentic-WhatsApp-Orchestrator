// hooks/useSSE.ts — Shared SSE connection with exponential backoff + connection state

import { useEffect, useRef, useCallback, useState } from 'react';
import { getSSEUrl } from '../api/client';
import type { SSEEvent } from '../types';

export type SSEConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

type SSEHandler = (event: SSEEvent) => void;

const MAX_BACKOFF_MS = 30_000;
const INITIAL_BACKOFF_MS = 1_000;

export function useSSE(tenantId: string | null, onEvent: SSEHandler) {
  const esRef = useRef<EventSource | null>(null);
  const handlerRef = useRef(onEvent);
  const retryCountRef = useRef(0);
  const mountedRef = useRef(true);
  const [connectionState, setConnectionState] = useState<SSEConnectionState>('disconnected');

  handlerRef.current = onEvent;

  const connect = useCallback(() => {
    if (!tenantId || !mountedRef.current) return;

    esRef.current?.close();

    setConnectionState('connecting');
    const url = getSSEUrl(tenantId);
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => {
      if (!mountedRef.current) return;
      retryCountRef.current = 0;
      setConnectionState('connected');
    };

    es.onmessage = (event) => {
      try {
        const parsed: SSEEvent = JSON.parse(event.data);
        if (parsed.type === 'connected') {
          setConnectionState('connected');
          retryCountRef.current = 0;
        } else if (parsed.type !== 'ping') {
          handlerRef.current(parsed);
        }
      } catch {
        // Ignore malformed events
      }
    };

    es.onerror = () => {
      es.close();
      if (!mountedRef.current) return;
      setConnectionState('error');

      // Exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s cap
      const backoff = Math.min(
        INITIAL_BACKOFF_MS * Math.pow(2, retryCountRef.current),
        MAX_BACKOFF_MS,
      );
      retryCountRef.current += 1;

      setTimeout(connect, backoff);
    };
  }, [tenantId]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      esRef.current?.close();
      setConnectionState('disconnected');
    };
  }, [connect]);

  return { connectionState };
}
