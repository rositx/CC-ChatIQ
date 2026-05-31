import React, { useState } from 'react';
import { useSessionStore } from 'opendesk-core';

interface ChatInputProps {
  sendMessage: (msg: any) => void;
}

const inputStyles = {
  form: {
    padding: '14px 16px',
    background: 'rgba(15, 23, 42, 0.7)',
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    backdropFilter: 'blur(10px)'
  } as React.CSSProperties,
  wrapper: {
    display: 'flex',
    alignItems: 'center',
    background: 'rgba(30, 41, 59, 0.55)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '24px',
    padding: '4px 6px 4px 16px',
    boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.15)',
    transition: 'border-color 0.25s, box-shadow 0.25s'
  } as React.CSSProperties,
  input: {
    flex: 1,
    background: 'transparent',
    border: 'none',
    color: '#f1f5f9',
    outline: 'none',
    fontSize: '13.5px',
    padding: '6px 0',
    marginRight: '8px'
  } as React.CSSProperties,
  button: {
    border: 'none',
    borderRadius: '50%',
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'transform 0.2s, opacity 0.2s, background 0.2s'
  } as React.CSSProperties
};

const getButtonStyle = (hasInput: boolean): React.CSSProperties => ({
  ...inputStyles.button,
  background: hasInput 
    ? 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' 
    : 'rgba(255, 255, 255, 0.04)',
  cursor: hasInput ? 'pointer' : 'default',
  boxShadow: hasInput ? '0 2px 8px rgba(37, 99, 235, 0.35)' : 'none'
});

const getWrapperStyle = (isFocused: boolean): React.CSSProperties => ({
  ...inputStyles.wrapper,
  borderColor: isFocused ? 'rgba(37, 99, 235, 0.35)' : 'rgba(255, 255, 255, 0.08)',
  boxShadow: isFocused 
    ? '0 0 10px rgba(37, 99, 235, 0.1), inset 0 2px 4px rgba(0, 0, 0, 0.15)' 
    : 'inset 0 2px 4px rgba(0, 0, 0, 0.15)'
});

const SendIcon: React.FC<{ hasInput: boolean }> = ({ hasInput }) => (
  <svg
    viewBox="0 0 24 24"
    width="14"
    height="14"
    stroke={hasInput ? '#ffffff' : '#64748b'}
    strokeWidth="2.5"
    fill="none"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ transition: 'stroke 0.2s' }}
  >
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

export const ChatInput: React.FC<ChatInputProps> = ({ sendMessage }) => {
  const { sessionId } = useSessionStore();
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const hasInput = !!input.trim();

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasInput || !sessionId) return;
    sendMessage({
      type: 'message',
      payload: { session_id: sessionId, role: 'customer', content: input.trim() }
    });
    setInput('');
  };

  return (
    <form onSubmit={handleSend} style={inputStyles.form}>
      <div 
        style={getWrapperStyle(isFocused)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          style={inputStyles.input}
        />
        <button
          type="submit"
          disabled={!hasInput}
          style={getButtonStyle(hasInput)}
          onMouseEnter={(e) => hasInput && (e.currentTarget.style.transform = 'scale(1.08)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <SendIcon hasInput={hasInput} />
        </button>
      </div>
    </form>
  );
};
