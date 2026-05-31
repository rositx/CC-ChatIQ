import React from 'react';
import { widgetStyles } from './WidgetStyles.js';

interface WidgetHeaderProps {
  onClose: () => void;
}

export const WidgetHeader: React.FC<WidgetHeaderProps> = ({ onClose }) => {
  const handleEnter = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
    e.currentTarget.style.transform = 'scale(1.05)';
  };

  const handleLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
    e.currentTarget.style.transform = 'scale(1)';
  };

  return (
    <div style={widgetStyles.header}>
      <div style={widgetStyles.headerTitleContainer}>
        <span style={widgetStyles.headerIcon}>⚡</span>
        <div>
          <div style={widgetStyles.headerTitle}>OpenDesk Chat</div>
          <div style={widgetStyles.headerSubtitle}>AI-Powered Assistance</div>
        </div>
      </div>
      <button 
        onClick={onClose}
        style={widgetStyles.closeButton}
        onMouseEnter={handleEnter}
        onMouseLeave={handleLeave}
      >
        &times;
      </button>
    </div>
  );
};
