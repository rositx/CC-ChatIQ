import React from 'react';
import { useQueueStore } from '../stores/queueStore.js';

export const CRMContext: React.FC<{ onResolve: (id: string) => void }> = ({ onResolve }) => {
  const { activeSessionId } = useQueueStore();
  if (!activeSessionId) return <div style={{ width: '280px', padding: '16px' }}>Select a conversation</div>;

  return (
    <div style={{ width: '280px', borderLeft: '1px solid rgba(255,255,255,0.06)', padding: '16px' }}>
      <h3>Customer Context</h3>
      <p><strong>Session:</strong> {activeSessionId.slice(0, 8)}</p>
      <button 
        onClick={() => onResolve(activeSessionId)} 
        style={{ width: '100%', padding: '8px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', marginTop: '20px' }}
      >
        Mark as Resolved
      </button>
    </div>
  );
};
