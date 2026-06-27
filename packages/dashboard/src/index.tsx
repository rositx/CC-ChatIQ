import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { MessageStream } from "./components/MessageStream.js";
import { QueuePanel } from "./components/QueuePanel.js";
import { CRMContext } from "./components/CRMContext.js";
import { AgentInput } from "./components/AgentInput.js";
import { useQueueStore } from "./stores/queueStore.js";
import { useMessageStore, getApiBaseUrl, getWsBaseUrl, LOCAL_TESTING } from "@opendesk/core";
import { AnalyticsPanel } from "./components/AnalyticsPanel.js";
import { SandboxPanel } from "./components/SandboxPanel.js";

export const DASHBOARD_VERSION = "1.0.0";
export * from "./components/MessageStream.js";
export * from "./components/MessageBubble.js";
export * from "./components/QueuePanel.js";
export * from "./components/CRMContext.js";
export * from "./components/AgentInput.js";
export * from "./stores/queueStore.js";

const DashboardApp: React.FC = () => {
  const { queue, setQueue, addQueueItem, removeQueueItem, activeSessionId, setActiveSessionId } = useQueueStore();
  const { setMessages, appendMessage } = useMessageStore();
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [activeTab, setActiveTab] = useState<"chat" | "analytics" | "sandbox">("chat");

  // 1. Fetch initial queue list on mount
  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/queue`, {
          headers: {
            "Authorization": "Bearer sandbox-token"
          }
        });
        if (response.ok) {
          const data = await response.json();
          setQueue(data);
        }
      } catch (err) {
        console.error("Failed to fetch initial queue:", err);
      }
    };
    fetchQueue();
  }, [setQueue]);

  // 2. Establish real-time WebSocket connection
  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      Notification.requestPermission();
    }

    const agentId = "00000000-0000-0000-0000-000000000000";
    const token = "sandbox-token";
    const socket = new WebSocket(`${getWsBaseUrl()}/ws/agent/${agentId}?token=${token}`);

    socket.onopen = () => {
      console.log("Agent WebSocket connected!");
    };

    socket.onmessage = (event) => {
      try {
        const frame = JSON.parse(event.data);
        console.log("Agent WS received:", frame);
        if (frame.type === "queue_update") {
          const { session_id, status, trigger } = frame.payload;
          if (status === "escalated") {
            addQueueItem({
              id: session_id,
              trigger: trigger || "escalated",
              escalated_at: new Date().toISOString()
            });
          } else if (status === "claimed" || status === "resolved") {
            removeQueueItem(session_id);
            if (activeSessionId === session_id) {
              setActiveSessionId(null);
              setMessages([]);
            }
          }
        } else if (frame.type === "session_transferred") {
          const { session_id, to_agent_id } = frame.payload;
          const myId = "00000000-0000-0000-0000-000000000000";
          if (to_agent_id === myId) {
            if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
              new Notification("New Transferred Conversation Assigned!");
            }
            addQueueItem({
              id: session_id,
              trigger: "manual_transfer",
              escalated_at: new Date().toISOString()
            });
          } else {
            removeQueueItem(session_id);
            if (activeSessionId === session_id) {
              setActiveSessionId(null);
              setMessages([]);
            }
          }
        } else if (frame.type === "message") {
          const msg = frame.payload;
          if (msg.session_id === activeSessionId) {
            appendMessage(msg);
          }
        }
      } catch (err) {
        console.error("Error processing Agent WS frame:", err);
      }
    };

    socket.onclose = () => {
      console.log("Agent WebSocket disconnected!");
    };

    setWs(socket);

    return () => {
      socket.close();
    };
  }, [activeSessionId, addQueueItem, removeQueueItem, setActiveSessionId, setMessages, appendMessage]);

  // 3. Load historical messages when selecting a session
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }
    const fetchHistory = async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/sessions/${activeSessionId}`, {
          headers: {
            "Authorization": "Bearer sandbox-token"
          }
        });
        if (response.ok) {
          const data = await response.json();
          setMessages(data);
        }
      } catch (err) {
        console.error("Failed to load historical messages:", err);
      }
    };
    fetchHistory();
  }, [activeSessionId, setMessages]);

  // 4. Handle session claim
  const handleClaim = async (id: string) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/queue/${id}/claim`, {
        method: "POST",
        headers: {
          "Authorization": "Bearer sandbox-token"
        }
      });
      if (response.ok) {
        setActiveSessionId(id);
      }
    } catch (err) {
      console.error("Failed to claim session:", err);
    }
  };

  // 5. Handle session resolve
  const handleResolve = async (id: string) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/sessions/${id}/resolve`, {
        method: "POST",
        headers: {
          "Authorization": "Bearer sandbox-token"
        }
      });
      if (response.ok) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to resolve session:", err);
    }
  };

  // 6. Handle agent message send
  const handleSend = (text: string) => {
    if (!activeSessionId || !ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({
      type: "message",
      payload: {
        session_id: activeSessionId,
        content: text
      }
    }));
  };

  const renderDashboardOnly = () => {
    return (
      <div style={{ display: "flex", flex: 1, overflow: "hidden", height: "100%" }}>
        <QueuePanel token="sandbox-token" onClaim={handleClaim} />
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <div style={{ flex: 1, overflow: "hidden" }}>
            <MessageStream />
          </div>
          <AgentInput onSend={handleSend} />
        </div>
        <CRMContext onResolve={handleResolve} />
      </div>
    );
  };

  return (
    <div style={{ height: "100vh", background: "#0f172a", color: "#ffffff", display: "flex", flexDirection: "column", fontFamily: "sans-serif" }}>
      <header style={{ padding: "16px", background: "#1e293b", borderBottom: "1px solid rgba(255,255,255,0.06)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0, fontSize: "18px" }}>CC-ChatIQ Agent Dashboard</h1>
        <nav style={{ display: "flex", gap: "8px" }}>
          <button 
            onClick={() => setActiveTab("chat")} 
            style={{ 
              padding: "6px 12px", 
              background: activeTab === "chat" ? "#3b82f6" : "transparent", 
              color: "#fff", 
              border: "1px solid rgba(255,255,255,0.1)", 
              borderRadius: "4px", 
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 600
            }}
          >
            Active Chat
          </button>
          <button 
            onClick={() => setActiveTab("analytics")} 
            style={{ 
              padding: "6px 12px", 
              background: activeTab === "analytics" ? "#3b82f6" : "transparent", 
              color: "#fff", 
              border: "1px solid rgba(255,255,255,0.1)", 
              borderRadius: "4px", 
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 600
            }}
          >
            Analytics
          </button>
          <button 
            onClick={() => setActiveTab("sandbox")} 
            style={{ 
              padding: "6px 12px", 
              background: activeTab === "sandbox" ? "#3b82f6" : "transparent", 
              color: "#fff", 
              border: "1px solid rgba(255,255,255,0.1)", 
              borderRadius: "4px", 
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 600
            }}
          >
            Sandbox Playground
          </button>
        </nav>
        <div style={{ fontSize: "12px", opacity: 0.6 }}>Connected to Database (Port 5434)</div>
      </header>
      {activeTab === "chat" && renderDashboardOnly()}
      {activeTab === "analytics" && (
        <div style={{ flex: 1, overflow: "hidden" }}>
          <AnalyticsPanel />
        </div>
      )}
      {activeTab === "sandbox" && (
        <SandboxPanel renderDashboard={renderDashboardOnly} />
      )}
    </div>
  );
};

const appElement = document.getElementById("app");
if (appElement) {
  ReactDOM.createRoot(appElement).render(
    <React.StrictMode>
      <DashboardApp />
    </React.StrictMode>
  );
}
