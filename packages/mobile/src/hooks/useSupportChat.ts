import { useEffect } from "react";
import { useWebSocket } from "@opendesk/core/dist/hooks/useWebSocket";
import { useMessageStore } from "@opendesk/core/dist/stores/messageStore";
import { useSessionStore } from "@opendesk/core/dist/stores/sessionStore";

interface UseSupportChatConfig {
  tenantId: string;
  sessionId: string;
  websocketUrl: string;
  token: string;
}

export function useSupportChat({ tenantId, sessionId, websocketUrl, token }: UseSupportChatConfig) {
  const setSession = useSessionStore((state) => state.setSession);

  // Initialize the session store with credentials so that core hooks utilize them
  useEffect(() => {
    if (token && sessionId) {
      setSession(token, sessionId);
    }
  }, [token, sessionId, setSession]);

  const { sendMessage } = useWebSocket(websocketUrl);
  const messages = useMessageStore((state) => state.messages);
  const connectionStatus = useSessionStore((state) => state.connectionStatus);
  const isConnected = connectionStatus === "connected";

  const sendTextMessage = (content: string) => {
    sendMessage({ type: "message", payload: { content } });
  };

  const escalateToAgent = () => {
    sendMessage({ type: "escalate", payload: {} });
  };

  return {
    messages,
    isConnected,
    connectionStatus,
    sendTextMessage,
    escalateToAgent,
  };
}
