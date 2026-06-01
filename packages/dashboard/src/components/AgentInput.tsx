import React, { useState } from 'react';

export const AgentInput: React.FC<{ onSend: (text: string) => void }> = ({ onSend }) => {
  const [text, setText] = useState('');
  const handleSend = () => {
    if (!text.trim()) return;
    onSend(text);
    setText('');
  };
  return (
    <div style={{ display: 'flex', padding: '16px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
      <input 
        value={text} 
        onChange={(e) => setText(e.target.value)} 
        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        style={{ flex: 1, padding: '8px', background: '#0f172a', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px' }}
      />
      <button onClick={handleSend} style={{ marginLeft: '10px', padding: '8px 16px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
        Send
      </button>
    </div>
  );
};
