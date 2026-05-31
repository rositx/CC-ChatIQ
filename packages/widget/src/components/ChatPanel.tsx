import React, { useRef, useEffect } from 'react';
import { useMessageStore } from 'cc-chatiq-core';
import { MessageBubble } from './MessageBubble.js';
import { ChatHeader } from './ChatHeader.js';
import { ChatInput } from './ChatInput.js';

interface ChatPanelProps {
  sendMessage: (msg: any) => void;
}

const panelStyles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    background: 'radial-gradient(circle at top left, #0f172a 0%, #020617 100%)',
    position: 'relative',
    overflow: 'hidden'
  } as React.CSSProperties,
  messagesList: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column'
  } as React.CSSProperties,
  welcomeContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    color: '#64748b',
    fontSize: '13px',
    textAlign: 'center',
    padding: '24px'
  } as React.CSSProperties,
  welcomeIcon: {
    fontSize: '32px',
    marginBottom: '10px',
    opacity: 0.6
  } as React.CSSProperties,
  welcomeTitle: {
    fontWeight: 600,
    color: '#94a3b8',
    marginBottom: '4px'
  } as React.CSSProperties,
  welcomeText: {
    lineHeight: '1.4'
  } as React.CSSProperties
};

const CustomStyles: React.FC = () => (
  <style>{`
    .cc-chatiq-messages-container::-webkit-scrollbar {
      width: 5px;
    }
    .cc-chatiq-messages-container::-webkit-scrollbar-track {
      background: transparent;
    }
    .cc-chatiq-messages-container::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.08);
      border-radius: 4px;
    }
    .cc-chatiq-messages-container::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.15);
    }
    @keyframes cc-chatiq-pulse-glow {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.5; transform: scale(0.95); }
    }
  `}</style>
);

const WelcomePlaceholder: React.FC = () => (
  <div style={panelStyles.welcomeContainer}>
    <div style={panelStyles.welcomeIcon}>💬</div>
    <div style={panelStyles.welcomeTitle}>Welcome to Chat Support</div>
    <div style={panelStyles.welcomeText}>
      Ask us anything. Our AI agent and support team are online to assist you.
    </div>
  </div>
);

export const ChatPanel: React.FC<ChatPanelProps> = ({ sendMessage }) => {
  const { messages } = useMessageStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div style={panelStyles.container}>
      <CustomStyles />
      <ChatHeader />
      <div className="cc-chatiq-messages-container" style={panelStyles.messagesList}>
        {messages.length === 0 ? (
          <WelcomePlaceholder />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput sendMessage={sendMessage} />
    </div>
  );
};
