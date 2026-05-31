import React from "react";
import ReactDOM from "react-dom/client";
import { MessageStream } from "./components/MessageStream.js";
import { useMessageStore } from "@opendesk/core";

export const DASHBOARD_VERSION = "1.0.0";
export * from "./components/MessageStream.js";
export * from "./components/MessageBubble.js";

// Mount the React application to the DOM if running in the browser
const appElement = document.getElementById("app");
if (appElement) {
  // Populate the Zustand store with some initial mock messages to showcase the layout
  const store = useMessageStore.getState();
  store.setMessages([
    {
      id: "msg-1",
      session_id: "session-abc",
      role: "customer",
      content: "Hello, the product is broken and I need a refund immediately.",
      created_at: new Date(Date.now() - 60000).toISOString(),
    },
    {
      id: "msg-2",
      session_id: "session-abc",
      role: "ai",
      content: "Connecting you with a support representative...",
      created_at: new Date(Date.now() - 30000).toISOString(),
    },
  ]);

  // Simulate active real-time token streaming with the shell allocator guard and auto-scroll pinning
  const streamTokens = [
    "Sure, ", "I ", "can ", "help ", "you ", "with ", "that. ",
    "Let ", "me ", "pull ", "up ", "your ", "account ", "details ",
    "and ", "see ", "what ", "happened ", "to ", "your ", "order. ",
    "Could ", "you ", "please ", "verify ", "your ", "email ",
    "address ", "so ", "we ", "can ", "process ", "the ", "refund ",
    "request ", "transaction ", "smoothly?"
  ];

  let tokenIndex = 0;
  const interval = setInterval(() => {
    if (tokenIndex < streamTokens.length) {
      // Use appendToken which leverages the stream allocator guard on first chunk arrival
      store.appendToken("msg-3", streamTokens[tokenIndex], "agent");
      tokenIndex++;
    } else {
      clearInterval(interval);
    }
  }, 200);

  ReactDOM.createRoot(appElement).render(
    <React.StrictMode>
      <div style={{ height: "100vh", background: "#0f172a", color: "#ffffff", display: "flex", flexDirection: "column", fontFamily: "sans-serif" }}>
        <header style={{ padding: "16px", background: "#1e293b", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <h1 style={{ margin: 0, fontSize: "18px" }}>CC-ChatIQ Agent Dashboard Preview</h1>
        </header>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <MessageStream />
        </div>
      </div>
    </React.StrictMode>
  );
}
