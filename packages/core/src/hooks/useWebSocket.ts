import { useEffect, useRef, useCallback, MutableRefObject } from 'react';
import { useSessionStore } from '../stores/sessionStore.js';
import { useMessageStore } from '../stores/messageStore.js';
import { WS_RECONNECT_BASE_MS, WS_RECONNECT_MAX_MS, WS_HEARTBEAT_INTERVAL_MS } from '../constants.js';
import { Message } from '../types.js';

type HeartbeatInterval = ReturnType<typeof setInterval> | null;

function calculateBackoffDelay(attempt: number): number {
  const delay = Math.min(WS_RECONNECT_BASE_MS * Math.pow(2, attempt), WS_RECONNECT_MAX_MS);
  const jitter = delay * 0.2 * (Math.random() * 2 - 1);
  return delay + jitter;
}

function startHeartbeat(ws: WebSocket, intervalRef: MutableRefObject<HeartbeatInterval>) {
  intervalRef.current = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }, WS_HEARTBEAT_INTERVAL_MS);
}

function handleSocketMessage(
  event: MessageEvent,
  appendMessage: (message: Message) => void,
  appendToken: (messageId: string, token: string, role?: 'ai' | 'agent') => void
) {
  try {
    const frame = JSON.parse(event.data);
    if (frame.type === 'message') {
      appendMessage(frame.payload);
    } else if (frame.type === 'token') {
      appendToken(frame.payload.message_id, frame.payload.token, frame.payload.role);
    }
  } catch (error) {
    console.error('Error handling socket message:', error);
  }
}

async function syncHistoryAndFlush(
  sessionId: string,
  token: string,
  ws: WebSocket,
  offlineQueueRef: MutableRefObject<unknown[]>,
  setConnectionStatus: (status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected') => void
) {
  try {
    const response = await fetch(`/api/v1/sessions/${sessionId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    if (!response.ok) throw new Error("History sync failed");

    const historicalMessages = await response.json();
    useMessageStore.getState().mergeMessages(historicalMessages);

    const queue = offlineQueueRef.current;
    while (queue.length > 0 && ws.readyState === WebSocket.OPEN) {
      const pending = queue.shift();
      if (pending) {
        ws.send(JSON.stringify(pending));
      }
    }
    setConnectionStatus('connected');
  } catch (error) {
    console.error("Critical recovery synchronization error:", error);
    setConnectionStatus('connected');
  }
}

interface SocketEventProps {
  sessionId: string;
  token: string;
  offlineQueueRef: MutableRefObject<unknown[]>;
  setConnectionStatus: (status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected') => void;
  appendMessage: (message: Message) => void;
  appendToken: (messageId: string, token: string, role?: 'ai' | 'agent') => void;
  attemptRef: MutableRefObject<number>;
  heartbeatIntervalRef: MutableRefObject<HeartbeatInterval>;
  reconnect: () => void;
}

function bindSocketEvents(
  ws: WebSocket,
  activeRef: { current: boolean },
  props: SocketEventProps
) {
  ws.onopen = () => {
    if (!activeRef.current) return;
    props.attemptRef.current = 0;
    startHeartbeat(ws, props.heartbeatIntervalRef);
    syncHistoryAndFlush(props.sessionId, props.token, ws, props.offlineQueueRef, props.setConnectionStatus);
  };
  ws.onmessage = (event) => {
    if (activeRef.current) {
      handleSocketMessage(event, props.appendMessage, props.appendToken);
    }
  };
  ws.onclose = () => {
    if (props.heartbeatIntervalRef.current) clearInterval(props.heartbeatIntervalRef.current);
    if (!activeRef.current) return;
    props.setConnectionStatus('disconnected');
    const nextInterval = calculateBackoffDelay(props.attemptRef.current);
    props.attemptRef.current += 1;
    setTimeout(props.reconnect, nextInterval);
  };
}

interface SetupProps {
  url: string;
  token: string | null;
  sessionId: string | null;
  socketRef: MutableRefObject<WebSocket | null>;
  attemptRef: MutableRefObject<number>;
  heartbeatIntervalRef: MutableRefObject<HeartbeatInterval>;
  offlineQueueRef: MutableRefObject<unknown[]>;
  setConnectionStatus: (status: 'connecting' | 'connected' | 'reconnecting' | 'disconnected') => void;
  appendMessage: (message: Message) => void;
  appendToken: (messageId: string, token: string, role?: 'ai' | 'agent') => void;
}

function useWebSocketSetup(props: SetupProps) {
  const { url, token, sessionId, socketRef, attemptRef, heartbeatIntervalRef, offlineQueueRef, setConnectionStatus, appendMessage, appendToken } = props;
  useEffect(() => {
    if (!token || !sessionId) return;
    const activeRef = { current: true };
    const connect = () => {
      if (!activeRef.current) return;
      setConnectionStatus('connecting');
      const ws = new WebSocket(`${url}/${sessionId}?token=${token}`);
      socketRef.current = ws;
      bindSocketEvents(ws, activeRef, {
        sessionId,
        token,
        offlineQueueRef,
        setConnectionStatus,
        appendMessage,
        appendToken,
        attemptRef,
        heartbeatIntervalRef,
        reconnect: connect,
      });
    };
    connect();
    return () => {
      activeRef.current = false;
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
      socketRef.current?.close();
    };
  }, [url, token, sessionId, socketRef, attemptRef, heartbeatIntervalRef, offlineQueueRef, setConnectionStatus, appendMessage, appendToken]);
}

export function useWebSocket(url: string) {
  const socketRef = useRef<WebSocket | null>(null);
  const attemptRef = useRef(0);
  const heartbeatIntervalRef = useRef<HeartbeatInterval>(null);
  const offlineQueueRef = useRef<unknown[]>([]);
  const { token, sessionId, setConnectionStatus } = useSessionStore();
  const { appendMessage, appendToken } = useMessageStore();

  useWebSocketSetup({
    url,
    token,
    sessionId,
    socketRef,
    attemptRef,
    heartbeatIntervalRef,
    offlineQueueRef,
    setConnectionStatus,
    appendMessage,
    appendToken,
  });

  const sendMessage = useCallback((msg: unknown) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(msg));
    } else {
      offlineQueueRef.current.push(msg);
    }
  }, []);

  return { socket: socketRef.current, sendMessage };
}
