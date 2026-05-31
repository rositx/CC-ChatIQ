import React from 'react';
import { useSessionStore } from 'cc-chatiq-core';

const headerStyles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px 18px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    backdropFilter: 'blur(8px)'
  } as React.CSSProperties,
  indicator: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    marginRight: '8px',
    animation: 'cc-chatiq-pulse-glow 1.8s infinite ease-in-out'
  } as React.CSSProperties,
  text: {
    fontSize: '11px',
    fontWeight: 500,
    color: '#94a3b8',
    letterSpacing: '0.02em'
  } as React.CSSProperties
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'connected': return '#10b981'; // green
    case 'connecting':
    case 'reconnecting': return '#f59e0b'; // amber
    case 'disconnected': return '#ef4444'; // red
    default: return '#64748b';
  }
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'connected': return 'Online';
    case 'connecting': return 'Connecting...';
    case 'reconnecting': return 'Reconnecting...';
    case 'disconnected': return 'Offline';
    default: return 'Offline';
  }
};

export const ChatHeader: React.FC = () => {
  const { connectionStatus } = useSessionStore();
  const color = getStatusColor(connectionStatus);

  return (
    <div style={headerStyles.container}>
      <div style={{
        ...headerStyles.indicator,
        backgroundColor: color,
        boxShadow: `0 0 6px ${color}`
      }} />
      <span style={headerStyles.text}>
        {getStatusText(connectionStatus)}
      </span>
    </div>
  );
};
