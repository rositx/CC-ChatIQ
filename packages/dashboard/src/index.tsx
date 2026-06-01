import React from "react";
import ReactDOM from "react-dom/client";
import { MessageStream } from "./components/MessageStream.js";
import { QueuePanel } from "./components/QueuePanel.js";
import { CRMContext } from "./components/CRMContext.js";
import { AgentInput } from "./components/AgentInput.js";

export const DASHBOARD_VERSION = "1.0.0";
export * from "./components/MessageStream.js";
export * from "./components/MessageBubble.js";
export * from "./components/QueuePanel.js";
export * from "./components/CRMContext.js";
export * from "./components/AgentInput.js";
export * from "./stores/queueStore.js";

// Mount the React application to the DOM if running in the browser
const appElement = document.getElementById("app");
if (appElement) {
  ReactDOM.createRoot(appElement).render(
    <React.StrictMode>
      <div style={{ height: "100vh", background: "#0f172a", color: "#ffffff", display: "flex", flexDirection: "column", fontFamily: "sans-serif" }}>
        <header style={{ padding: "16px", background: "#1e293b", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <h1 style={{ margin: 0, fontSize: "18px" }}>CC-ChatIQ Agent Dashboard Preview</h1>
        </header>
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          <QueuePanel token="" onClaim={(id) => console.log("Claiming", id)} />
          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <div style={{ flex: 1, overflow: "hidden" }}>
              <MessageStream />
            </div>
            <AgentInput onSend={(text) => console.log("Sending", text)} />
          </div>
          <CRMContext onResolve={(id) => console.log("Resolving", id)} />
        </div>
      </div>
    </React.StrictMode>
  );
}
