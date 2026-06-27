import React, { useState } from "react";
import { Widget } from "cc-chatiq-widget";
import { getApiBaseUrl } from "@opendesk/core";

export const SandboxPanel: React.FC<{ renderDashboard: () => React.ReactNode }> = ({ renderDashboard }) => {
  const [resetting, setResetting] = useState(false);

  const handleReset = async () => {
    setResetting(true);
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/sessions/reset`, {
        method: "POST",
        headers: { "Authorization": "Bearer sandbox-token" }
      });
      if (response.ok) {
        alert("Sandbox states cleared successfully!");
        window.location.reload();
      }
    } catch (err) {
      console.error("Reset failed:", err);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100%", background: "#0b0f19" }}>
      <div style={{ padding: "8px 16px", background: "#111827", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontSize: "13px", color: "rgba(255,255,255,0.7)" }}>Interactive Playground Sandbox Mode</div>
        <button 
          onClick={handleReset} 
          disabled={resetting}
          style={{
            padding: "6px 12px", 
            background: "#ef4444", 
            color: "#fff", 
            border: "none", 
            borderRadius: "4px", 
            cursor: "pointer", 
            fontSize: "12px",
            fontWeight: 600
          }}
        >
          {resetting ? "Resetting..." : "Reset Sandbox Database"}
        </button>
      </div>
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Customer View */}
        <div style={{ flex: 1, borderRight: "1px solid rgba(255,255,255,0.06)", display: "flex", flexDirection: "column", position: "relative", padding: "16px", background: "#0f172a" }}>
          <div style={{ fontSize: "14px", fontWeight: 600, opacity: 0.6, marginBottom: "8px", color: "#fff" }}>Customer Interface Mockup</div>
          <div style={{ flex: 1, border: "1px dashed rgba(255,255,255,0.1)", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
            <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "13px" }}>Click the bottom-right chat bubble to chat with the AI/Agent</div>
            <Widget wsUrl="ws://localhost:8000/ws/chat" />
          </div>
        </div>
        {/* Agent View */}
        <div style={{ width: "65%", display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: "14px", fontWeight: 600, opacity: 0.6, padding: "16px 16px 0 16px", color: "#fff" }}>Agent Dashboard Interface</div>
          <div style={{ flex: 1 }}>
            {renderDashboard()}
          </div>
        </div>
      </div>
    </div>
  );
};
