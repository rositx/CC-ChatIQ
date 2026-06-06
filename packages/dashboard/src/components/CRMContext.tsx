import React, { useEffect, useState } from 'react';
import { useQueueStore } from '../stores/queueStore.js';
import { getApiBaseUrl } from "@opendesk/core";

interface SessionMetadata {
  id: string;
  customer_id: string;
  agent_id: string | null;
  status: string;
  escalation_trigger: string | null;
  peak_score: number | null;
}

export const CRMContext: React.FC<{ onResolve: (id: string) => void }> = ({ onResolve }) => {
  const { activeSessionId } = useQueueStore();
  const [metadata, setMetadata] = useState<SessionMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState<{agent_id: string, active_chats: number}[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);

  const fetchOnlineAgents = async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/agents/online`, {
        headers: { "Authorization": "Bearer sandbox-token" }
      });
      if (response.ok) {
        const data = await response.json();
        setAgents(data);
      }
    } catch (err) {
      console.error("Failed to fetch online agents:", err);
    }
  };

  const handleTransfer = async (targetAgentId: string) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/sessions/${activeSessionId}/transfer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer sandbox-token"
        },
        body: JSON.stringify({ target_agent_id: targetAgentId })
      });
      if (response.ok && activeSessionId) {
        onResolve(activeSessionId);
        setShowDropdown(false);
      }
    } catch (err) {
      console.error("Failed to transfer session:", err);
    }
  };

  useEffect(() => {
    if (!activeSessionId) {
      setMetadata(null);
      return;
    }
    const fetchMetadata = async () => {
      setLoading(true);
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/sessions/${activeSessionId}/metadata`, {
          headers: {
            "Authorization": "Bearer sandbox-token"
          }
        });
        if (response.ok) {
          const data = await response.json();
          setMetadata(data);
        }
      } catch (err) {
        console.error("Failed to fetch session metadata:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchMetadata();
  }, [activeSessionId]);

  if (!activeSessionId) {
    return (
      <div style={{ width: '280px', padding: '24px', color: 'rgba(255,255,255,0.35)', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', borderLeft: '1px solid rgba(255,255,255,0.06)' }}>
        <div>Select a conversation to view customer context</div>
      </div>
    );
  }

  // Sentiment Metrics Styling (curated modern color palettes)
  let sentimentLabel = "Neutral / Stable";
  let sentimentColor = "#38bdf8"; // sky blue
  let sentimentBg = "linear-gradient(135deg, rgba(56, 189, 248, 0.1) 0%, rgba(56, 189, 248, 0.03) 100%)";
  let sentimentBorder = "rgba(56, 189, 248, 0.25)";
  let meterPercentage = 50;

  if (metadata && metadata.peak_score !== null) {
    const score = metadata.peak_score;
    meterPercentage = Math.round(score * 100);
    if (score >= 0.7) {
      sentimentLabel = "Highly Frustrated";
      sentimentColor = "#f43f5e"; // rose red
      sentimentBg = "linear-gradient(135deg, rgba(244, 63, 94, 0.15) 0%, rgba(244, 63, 94, 0.03) 100%)";
      sentimentBorder = "rgba(244, 63, 94, 0.35)";
    } else if (score >= 0.3) {
      sentimentLabel = "Frustrated";
      sentimentColor = "#f59e0b"; // warm amber
      sentimentBg = "linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.03) 100%)";
      sentimentBorder = "rgba(245, 158, 11, 0.3)";
    } else {
      sentimentLabel = "Calm & Satisfied";
      sentimentColor = "#10b981"; // vibrant emerald green
      sentimentBg = "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.03) 100%)";
      sentimentBorder = "rgba(16, 185, 129, 0.3)";
    }
  }

  return (
    <div style={{ width: '280px', borderLeft: '1px solid rgba(255,255,255,0.06)', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto' }}>
      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', opacity: 0.85 }}>Customer Context</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.4 }}>Active Session</div>
        <div style={{ fontSize: '13px', fontFamily: 'monospace', background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.85)' }}>
          {activeSessionId}
        </div>
      </div>

      {loading ? (
        <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="spinner" style={{ width: '12px', height: '12px', borderRadius: '50%', border: '2px solid rgba(255,255,255,0.2)', borderTopColor: '#38bdf8', animation: 'spin 1s linear infinite' }} />
          Loading customer metrics...
        </div>
      ) : metadata ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.4 }}>Escalation Reason</div>
            <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.85)', background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.04)', textTransform: 'capitalize' }}>
              {metadata.escalation_trigger ? metadata.escalation_trigger.replace('_', ' ') : 'N/A'}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.4 }}>Customer Sentiment Matrix</div>
            
            <div style={{ 
              background: sentimentBg, 
              border: `1px solid ${sentimentBorder}`, 
              borderRadius: '8px', 
              padding: '16px', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '12px',
              transition: 'all 0.3s ease'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '14px', fontWeight: 'bold', color: sentimentColor }}>{sentimentLabel}</span>
                <span style={{ fontSize: '12px', opacity: 0.7, color: sentimentColor }}>{metadata.peak_score !== null ? `${meterPercentage}%` : 'N/A'}</span>
              </div>
              
              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${meterPercentage}%`, height: '100%', background: sentimentColor, borderRadius: '3px', transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)' }} />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.4)', fontSize: '13px', textAlign: 'center' }}>
          Sentiment score not calculated yet
        </div>
      )}

      <div style={{ position: 'relative', width: '100%', marginTop: 'auto', marginBottom: '10px' }}>
        <button 
          onClick={() => { setShowDropdown(!showDropdown); if(!showDropdown) fetchOnlineAgents(); }}
          style={{
            width: '100%', 
            padding: '10px', 
            background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)', 
            color: '#fff', 
            border: 'none', 
            borderRadius: '6px', 
            cursor: 'pointer', 
            fontWeight: 600, 
            fontSize: '13px',
            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.15)',
            transition: 'transform 0.2s ease'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-1px)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; }}
        >
          Transfer Conversation
        </button>
        {showDropdown && (
          <div style={{
            position: 'absolute', 
            bottom: '100%', 
            left: 0, 
            width: '100%',
            background: '#1e293b', 
            border: '1px solid rgba(255,255,255,0.08)', 
            borderRadius: '6px',
            padding: '8px', 
            zIndex: 10, 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '4px',
            boxShadow: '0 -4px 12px rgba(0,0,0,0.3)',
            marginBottom: '4px'
          }}>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', paddingBottom: '4px', borderBottom: '1px solid rgba(255,255,255,0.05)', fontWeight: 600 }}>
              Select Agent:
            </div>
            {agents.length === 0 ? (
              <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', padding: '4px 0', textAlign: 'center' }}>No other agents online</div>
            ) : (
              agents.map(ag => (
                <div 
                  key={ag.agent_id}
                  onClick={() => handleTransfer(ag.agent_id)}
                  style={{ 
                    padding: '6px 8px', 
                    cursor: 'pointer', 
                    fontSize: '12px', 
                    color: '#60a5fa', 
                    borderRadius: '4px',
                    background: 'transparent',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                >
                  Agent {ag.agent_id.slice(0, 5)} ({ag.active_chats} active)
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <button 
        onClick={() => onResolve(activeSessionId)} 
        style={{ 
          width: '100%', 
          padding: '10px', 
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 
          color: '#fff', 
          border: 'none', 
          borderRadius: '6px', 
          cursor: 'pointer', 
          fontWeight: 600, 
          fontSize: '13px',
          boxShadow: '0 4px 12px rgba(16, 185, 129, 0.15)',
          transition: 'transform 0.2s ease, opacity 0.2s ease'
        }}
        onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-1px)'; }}
        onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; }}
      >
        Mark as Resolved
      </button>
    </div>
  );
};

