import React, { useEffect, useState, useRef } from "react";
import { getApiBaseUrl } from "@opendesk/core";
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

interface AnalyticsData {
  total_sessions: number;
  escalations_by_trigger: Record<string, number>;
  average_wait_time_seconds: number;
  rag_fallback_count: number;
}

export const AnalyticsPanel: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await fetch(`${getApiBaseUrl()}/api/v1/analytics/summary`, {
          headers: { "Authorization": "Bearer sandbox-token" }
        });
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
      }
    };
    fetchAnalytics();
  }, []);

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    
    if (chartRef.current) {
      chartRef.current.destroy();
    }
    
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;
    
    const triggers = data.escalations_by_trigger;
    
    chartRef.current = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["CalmIQ Score", "User Request", "Keyword Trigger", "Manual Transfer"],
        datasets: [{
          data: [
            triggers.calmiq || 0,
            triggers.user_request || 0,
            triggers.keyword_trigger || 0,
            triggers.manual_transfer || 0
          ],
          backgroundColor: ["#f43f5e", "#38bdf8", "#f59e0b", "#10b981"],
          borderColor: "rgba(255,255,255,0.08)",
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#ffffff", boxWidth: 12, font: { family: "sans-serif", size: 12 } }
          }
        }
      }
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, [data]);

  if (!data) return <div style={{ padding: "24px", color: "rgba(255,255,255,0.5)" }}>Loading analytics...</div>;

  return (
    <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "24px", overflowY: "auto", height: "100%", width: "100%", boxSizing: "border-box" }}>
      <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 600, color: "#fff" }}>Analytics & Operations</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px" }}>
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "16px" }}>
          <div style={{ fontSize: "12px", opacity: 0.5 }}>Total Sessions</div>
          <div style={{ fontSize: "32px", fontWeight: "bold", marginTop: "8px" }}>{data.total_sessions}</div>
        </div>
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "16px" }}>
          <div style={{ fontSize: "12px", opacity: 0.5 }}>Avg. Wait Time</div>
          <div style={{ fontSize: "32px", fontWeight: "bold", marginTop: "8px", color: "#60a5fa" }}>
            {Math.round(data.average_wait_time_seconds)}s
          </div>
        </div>
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "16px" }}>
          <div style={{ fontSize: "12px", opacity: 0.5 }}>RAG Fallback Count</div>
          <div style={{ fontSize: "32px", fontWeight: "bold", marginTop: "8px", color: "#f43f5e" }}>
            {data.rag_fallback_count}
          </div>
        </div>
      </div>
      <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: "300px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "20px" }}>
          <h3 style={{ margin: "0 0 16px 0", fontSize: "14px", opacity: 0.7 }}>Escalation Trigger Ratios</h3>
          <div style={{ maxWidth: "260px", margin: "0 auto" }}>
            <canvas ref={canvasRef} />
          </div>
        </div>
      </div>
    </div>
  );
};
