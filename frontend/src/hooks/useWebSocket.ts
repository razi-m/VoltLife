import { useState, useEffect, useCallback, useRef } from 'react';
import { WS_URL } from '../lib/api';
import type { WSEvent } from '../lib/types';

interface UseWebSocketReturn {
  connected: boolean;
  lastEvent: WSEvent | null;
  events: WSEvent[];
}

export function useWebSocket(): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
  const [events, setEvents] = useState<WSEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (ev) => {
      try {
        const event: WSEvent = JSON.parse(ev.data);
        setLastEvent(event);
        setEvents((prev) => [...prev.slice(-49), event]);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 3 seconds
      reconnectTimerRef.current = window.setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, lastEvent, events };
}
