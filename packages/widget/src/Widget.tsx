import React, { useState, useEffect } from 'react';
import { useWebSocket, useSessionStore } from 'cc-chatiq-core';
import { ChatPanel } from './components/ChatPanel.js';
import { widgetStyles } from './components/WidgetStyles.js';
import { WidgetStylesInject } from './components/WidgetStylesInject.js';
import { FloatingBadge } from './components/FloatingBadge.js';
import { WidgetHeader } from './components/WidgetHeader.js';

interface WidgetProps {
  wsUrl?: string;
}

export const Widget: React.FC<WidgetProps> = ({ wsUrl = "ws://localhost:8000/ws/chat" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { token, sessionId, setSession } = useSessionStore();
  const { sendMessage } = useWebSocket(wsUrl);

  useEffect(() => {
    if (!sessionId || !token) {
      const savedSessionId = localStorage.getItem('cc_chatiq_session_id');
      const savedToken = localStorage.getItem('cc_chatiq_token');
      if (savedSessionId && savedToken) {
        setSession(savedToken, savedSessionId);
      } else {
        setSession('sandbox-token', '00000000-0000-0000-0000-000000000000');
      }
    }
  }, [sessionId, token, setSession]);

  return (
    <div style={widgetStyles.container}>
      <WidgetStylesInject />
      {isOpen ? (
        <div style={widgetStyles.panelContainer}>
          <WidgetHeader onClose={() => setIsOpen(false)} />
          <div style={widgetStyles.flowArea}>
            <ChatPanel sendMessage={sendMessage} />
          </div>
        </div>
      ) : (
        <FloatingBadge onClick={() => setIsOpen(true)} />
      )}
    </div>
  );
};
