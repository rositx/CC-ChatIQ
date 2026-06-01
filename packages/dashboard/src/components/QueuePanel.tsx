import React from 'react';
import { useQueueStore } from '../stores/queueStore.js';

export const QueuePanel: React.FC<{ token: string; onClaim: (id: string) => void }> = ({ token, onClaim }) => {
  const { queue, activeSessionId, setActiveSessionId } = useQueueStore();
  
  return (
    <div style={{ width: '300px', borderRight: '1px solid rgba(255,255,255,0.06)', padding: '16px', overflowY: 'auto' }}>
      <h3>Escalation Queue</h3>
      {queue.map((sess) => (
        <div 
          key={sess.id} 
          style={{ 
            padding: '12px', marginBottom: '10px', borderRadius: '8px', 
            background: activeSessionId === sess.id ? '#1e293b' : 'rgba(255,255,255,0.02)',
            cursor: 'pointer', border: '1px solid rgba(255,255,255,0.06)'
          }}
          onClick={() => setActiveSessionId(sess.id)}
        >
          <div><strong>ID:</strong> {sess.id.slice(0, 8)}</div>
          <div><strong>Trigger:</strong> {sess.trigger}</div>
          <button 
            onClick={(e) => { e.stopPropagation(); onClaim(sess.id); }} 
            style={{ marginTop: '8px', padding: '4px 8px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
          >
            Claim
          </button>
        </div>
      ))}
    </div>
  );
};
