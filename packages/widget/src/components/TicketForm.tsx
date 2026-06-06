import React, { useState } from 'react';

interface TicketFormProps {
  onSubmit: (email: string, message: string) => void;
}

export const TicketForm: React.FC<TicketFormProps> = ({ onSubmit }) => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim() && message.trim()) {
      onSubmit(email.trim(), message.trim());
    }
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      style={{ 
        padding: '24px', 
        background: 'rgba(30, 41, 59, 0.45)', 
        borderRadius: '12px', 
        border: '1px solid rgba(255, 255, 255, 0.08)', 
        margin: '16px',
        backdropFilter: 'blur(16px)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}
    >
      <div>
        <h4 style={{ margin: '0 0 4px 0', color: '#f8fafc', fontSize: '15px', fontWeight: 600 }}>Queue is Full</h4>
        <p style={{ margin: 0, color: '#94a3b8', fontSize: '12px', lineHeight: '1.4' }}>
          Our active queue is currently at capacity. Please submit your details below and a representative will follow up via email.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Email Address</label>
        <input 
          type="email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          placeholder="your@email.com" 
          required 
          style={{ 
            width: '100%', 
            padding: '10px 14px', 
            background: 'rgba(15, 23, 42, 0.45)', 
            border: '1px solid rgba(255, 255, 255, 0.08)', 
            borderRadius: '8px', 
            color: '#f8fafc',
            outline: 'none',
            fontSize: '13px',
            transition: 'border-color 0.2s'
          }}
          onFocus={(e) => e.target.style.borderColor = '#2563eb'}
          onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)'}
        />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Message</label>
        <textarea 
          value={message} 
          onChange={(e) => setMessage(e.target.value)} 
          placeholder="How can we help you?" 
          required 
          rows={4} 
          style={{ 
            width: '100%', 
            padding: '10px 14px', 
            background: 'rgba(15, 23, 42, 0.45)', 
            border: '1px solid rgba(255, 255, 255, 0.08)', 
            borderRadius: '8px', 
            color: '#f8fafc',
            outline: 'none',
            fontSize: '13px',
            resize: 'none',
            transition: 'border-color 0.2s'
          }}
          onFocus={(e) => e.target.style.borderColor = '#2563eb'}
          onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)'}
        />
      </div>

      <button 
        type="submit" 
        style={{ 
          width: '100%', 
          padding: '10px', 
          background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)', 
          color: '#fff', 
          border: 'none', 
          borderRadius: '8px', 
          cursor: 'pointer', 
          fontWeight: 600, 
          fontSize: '13px',
          boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)',
          transition: 'transform 0.15s ease'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
      >
        Submit Request
      </button>
    </form>
  );
};
