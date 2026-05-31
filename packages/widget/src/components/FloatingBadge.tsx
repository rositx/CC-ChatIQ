import React from 'react';
import { widgetStyles } from './WidgetStyles.js';

interface FloatingBadgeProps {
  onClick: () => void;
}

export const FloatingBadge: React.FC<FloatingBadgeProps> = ({ onClick }) => {
  const handleMouseEnter = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.style.transform = 'scale(1.08) translateY(-3px)';
    e.currentTarget.style.boxShadow = '0 12px 40px rgba(37, 99, 235, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.2)';
  };

  const handleMouseLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.style.transform = 'scale(1) translateY(0)';
    e.currentTarget.style.boxShadow = '0 8px 32px rgba(37, 99, 235, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.2)';
  };

  return (
    <button
      onClick={onClick}
      style={widgetStyles.badgeButton}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <svg
        viewBox="0 0 24 24"
        width="24"
        height="24"
        stroke="#ffffff"
        strokeWidth="2.5"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    </button>
  );
};
