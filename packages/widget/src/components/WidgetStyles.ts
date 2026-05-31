import React from 'react';

export const widgetStyles = {
  container: {
    position: 'fixed',
    bottom: '24px',
    right: '24px',
    zIndex: 99999,
    fontFamily: "system-ui, -apple-system, sans-serif"
  } as React.CSSProperties,
  panelContainer: {
    width: '380px',
    height: '600px',
    maxHeight: 'calc(90vh - 100px)',
    maxWidth: 'calc(100vw - 48px)',
    background: 'rgba(15, 23, 42, 0.95)',
    boxShadow: '0 20px 40px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.08)',
    borderRadius: '24px',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    animation: 'opendesk-widget-slide-up 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards'
  } as React.CSSProperties,
  header: {
    background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.8) 0%, rgba(29, 78, 216, 0.8) 100%)',
    padding: '16px 20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(12px)',
    position: 'relative',
    zIndex: 2
  } as React.CSSProperties,
  headerTitleContainer: {
    display: 'flex',
    alignItems: 'center'
  } as React.CSSProperties,
  headerIcon: {
    fontSize: '20px',
    marginRight: '10px'
  } as React.CSSProperties,
  headerTitle: {
    fontWeight: 700,
    fontSize: '15px',
    color: '#ffffff',
    letterSpacing: '0.01em'
  } as React.CSSProperties,
  headerSubtitle: {
    fontSize: '11px',
    color: 'rgba(255, 255, 255, 0.75)',
    marginTop: '2px'
  } as React.CSSProperties,
  closeButton: {
    background: 'rgba(255, 255, 255, 0.1)',
    border: 'none',
    color: '#ffffff',
    fontSize: '18px',
    lineHeight: '1',
    cursor: 'pointer',
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background 0.2s, transform 0.2s'
  } as React.CSSProperties,
  flowArea: {
    flex: 1
  } as React.CSSProperties,
  badgeButton: {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
    color: '#ffffff',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 8px 32px rgba(37, 99, 235, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.2)',
    fontSize: '24px',
    transition: 'transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.25s, background 0.25s',
    animation: 'opendesk-badge-pulse 2.5s infinite ease-in-out'
  } as React.CSSProperties
};
