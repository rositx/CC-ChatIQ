import React from 'react';
import ReactDOM from 'react-dom/client';
import { Widget } from './Widget.js';

export * from './components/MessageBubble.js';
export * from './components/ChatHeader.js';
export * from './components/ChatInput.js';
export * from './components/ChatPanel.js';
export * from './Widget.js';

const appElement = document.getElementById('app');
if (appElement) {
  ReactDOM.createRoot(appElement).render(
    React.createElement(React.StrictMode, null,
      React.createElement('div', {
        style: {
          height: '100vh',
          background: '#0f172a',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }
      },
        React.createElement(Widget, null)
      )
    )
  );
}
