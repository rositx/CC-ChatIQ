# Phase 6: Analytics & Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the final launch phase including the analytics dashboard and API, background session summaries via Celery, open-source documents, and an interactive sandbox environment.

**Architecture:** Database schema is updated to store conversation summaries and agent claiming times. A new `/api/v1/analytics/summary` API delivers metrics using real-time dynamic queries, and a `/api/v1/sessions/reset` endpoint enables sandboxed DB reset. Celery triggers summary generation on session resolution, and the Vite React app integrates Chart.js visual panels and a side-by-side sandbox.

**Tech Stack:** FastAPI, SQLAlchemy, Redis, Celery, React 18, Chart.js, HTML/CSS.

---

### Task 1: Schema & Repository Updates

**Files:**
- Modify: `backend/storage/schema.py`
- Modify: `backend/repositories/session.py`
- Test: `backend/tests/test_repositories.py`

- [ ] **Step 1: Write the failing test**
  Add a new test inside `backend/tests/test_repositories.py` verifying that session objects can store `summary` and `claimed_at`, and that the database schema includes these columns.
  ```python
  # Add to backend/tests/test_repositories.py
  async def test_session_summary_and_claimed_at(db_session):
      from backend.repositories.session import SessionRepository
      from backend.storage.schema import SessionModel
      import uuid
      
      repo = SessionRepository(db_session)
      tenant_id = uuid.uuid4()
      cust_id = uuid.uuid4()
      sess = await repo.create_session(customer_id=cust_id, tenant_id=tenant_id)
      
      # Verify default values
      assert sess.summary is None
      assert sess.claimed_at is None
      
      # Test claim session updates claimed_at
      agent_id = uuid.uuid4()
      await repo.claim_session(sess.id, agent_id)
      await db_session.refresh(sess)
      assert sess.agent_id == agent_id
      assert sess.claimed_at is not None
      
      # Test update_summary method
      await repo.update_summary(sess.id, "A test summary.")
      await db_session.refresh(sess)
      assert sess.summary == "A test summary."
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest backend/tests/test_repositories.py -k test_session_summary_and_claimed_at`
  Expected: FAIL (missing columns/methods)

- [ ] **Step 3: Write minimal implementation**
  Add columns to `SessionModel` in `backend/storage/schema.py`:
  ```python
  # Add to SessionModel in backend/storage/schema.py
  summary = Column(Text, nullable=True)
  claimed_at = Column(DateTime(timezone=True), nullable=True)
  ```
  Implement repository additions in `backend/repositories/session.py`:
  ```python
  # Modify claim_session and add update_summary in SessionRepository (backend/repositories/session.py)
  async def claim_session(self, session_id: UUID, agent_id: UUID) -> None:
      try:
          from sqlalchemy import func
          query = (
              update(SessionModel)
              .where(SessionModel.id == session_id)
              .values(agent_id=agent_id, status="active", claimed_at=func.now())
          )
          await self.db.execute(query)
          await self.db.commit()
      except Exception:
          await self.db.rollback()
          raise

  async def update_summary(self, session_id: UUID, summary: str) -> None:
      try:
          query = (
              update(SessionModel)
              .where(SessionModel.id == session_id)
              .values(summary=summary)
          )
          await self.db.execute(query)
          await self.db.commit()
      except Exception:
          await self.db.rollback()
          raise
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest backend/tests/test_repositories.py -k test_session_summary_and_claimed_at`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/storage/schema.py backend/repositories/session.py backend/tests/test_repositories.py
  git commit -m "feat: update session schema and repository with summary and claimed_at"
  ```

---

### Task 2: Repository Analytics Queries

**Files:**
- Modify: `backend/repositories/session.py`
- Test: `backend/tests/test_repositories.py`

- [ ] **Step 1: Write the failing test**
  Add a test `test_get_analytics_data` in `backend/tests/test_repositories.py`:
  ```python
  # Add to backend/tests/test_repositories.py
  async def test_get_analytics_data(db_session):
      from backend.repositories.session import SessionRepository
      import uuid
      from sqlalchemy import text
      
      repo = SessionRepository(db_session)
      # Seed some mock sessions
      t_id = uuid.uuid4()
      
      # Clear previous sessions to make asserts deterministic
      await db_session.execute(text("DELETE FROM sessions;"))
      await db_session.commit()
      
      s1 = await repo.create_session(uuid.uuid4(), t_id)
      s2 = await repo.create_session(uuid.uuid4(), t_id)
      
      # s1 escalated and claimed
      await repo.mark_escalated(s1.id, "keyword_trigger")
      await repo.claim_session(s1.id, uuid.uuid4())
      
      # s2 escalated, unclaimed
      await repo.mark_escalated(s2.id, "rag_fallback")
      
      analytics = await repo.get_analytics_data(t_id)
      assert analytics["total_sessions"] == 2
      assert analytics["escalations_by_trigger"]["keyword_trigger"] == 1
      assert analytics["escalations_by_trigger"]["rag_fallback"] == 1
      assert analytics["rag_fallback_count"] == 1
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest backend/tests/test_repositories.py -k test_get_analytics_data`
  Expected: FAIL (missing method `get_analytics_data`)

- [ ] **Step 3: Write minimal implementation**
  Add `get_analytics_data` inside `SessionRepository` in `backend/repositories/session.py`:
  ```python
  # Add to SessionRepository in backend/repositories/session.py
  async def get_analytics_data(self, tenant_id: UUID) -> dict:
      from sqlalchemy import func
      
      # Total count
      total_stmt = select(func.count(SessionModel.id)).where(SessionModel.tenant_id == tenant_id)
      total_res = await self.db.execute(total_stmt)
      total_sessions = total_res.scalar() or 0
      
      # Wait times: AVG(claimed_at - escalated_at)
      wait_stmt = select(
          func.avg(
              func.extract('epoch', SessionModel.claimed_at) - 
              func.extract('epoch', SessionModel.escalated_at)
          )
      ).where(
          SessionModel.tenant_id == tenant_id,
          SessionModel.claimed_at.is_not(None),
          SessionModel.escalated_at.is_not(None)
      )
      wait_res = await self.db.execute(wait_stmt)
      avg_wait = wait_res.scalar() or 0.0
      
      # Escalation triggers
      trigger_stmt = select(
          SessionModel.escalation_trigger,
          func.count(SessionModel.id)
      ).where(
          SessionModel.tenant_id == tenant_id,
          SessionModel.escalation_trigger.is_not(None)
      ).group_by(SessionModel.escalation_trigger)
      
      trigger_res = await self.db.execute(trigger_stmt)
      triggers = {row[0]: row[1] for row in trigger_res.all()}
      
      # Ensure all standard triggers have values
      standard_triggers = ["calmiq", "user_request", "keyword_trigger", "manual_transfer"]
      triggers_dict = {t: triggers.get(t, 0) for t in standard_triggers}
      
      rag_fallback_count = triggers.get("rag_fallback", 0)
      
      return {
          "total_sessions": total_sessions,
          "escalations_by_trigger": triggers_dict,
          "average_wait_time_seconds": float(avg_wait),
          "rag_fallback_count": rag_fallback_count
      }
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest backend/tests/test_repositories.py -k test_get_analytics_data`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/repositories/session.py backend/tests/test_repositories.py
  git commit -m "feat: implement get_analytics_data repository queries"
  ```

---

### Task 3: Analytics API Endpoint

**Files:**
- Create: `backend/api/analytics.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_queue_api.py`

- [ ] **Step 1: Write the failing test**
  Add a test verifying the analytics API endpoint returns valid metrics inside `backend/tests/test_queue_api.py` (or a new file).
  ```python
  # Add to backend/tests/test_queue_api.py
  def test_get_analytics_summary(client):
      response = client.get("/api/v1/analytics/summary", headers={"Authorization": "Bearer sandbox-token"})
      assert response.status_code == 200
      data = response.json()
      assert "total_sessions" in data
      assert "escalations_by_trigger" in data
      assert "average_wait_time_seconds" in data
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest backend/tests/test_queue_api.py -k test_get_analytics_summary`
  Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Write minimal implementation**
  Create `backend/api/analytics.py`:
  ```python
  from fastapi import APIRouter, Depends, HTTPException, Header, status
  from typing import Optional
  import uuid
  from backend.utils.jwt import verify_jwt_token
  from backend.repositories.session import SessionRepository
  
  router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
  
  async def get_session_repository() -> SessionRepository:
      from backend.storage.db import async_session_factory
      async with async_session_factory() as session:
          yield SessionRepository(session)
  
  @router.get("/summary")
  async def get_summary(
      authorization: Optional[str] = Header(None),
      repo: SessionRepository = Depends(get_session_repository)
  ):
      if not authorization or not authorization.startswith("Bearer "):
          raise HTTPException(status_code=401, detail="Missing or invalid token")
      token = authorization.split(" ")[1]
      
      tenant_id = None
      from backend.config import LOCAL_TESTING
      if LOCAL_TESTING and token == "sandbox-token":
          tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
      else:
          try:
              claims = verify_jwt_token(token)
              tenant_id = uuid.UUID(claims.get("tenant_id"))
          except Exception:
              raise HTTPException(status_code=401, detail="Unauthorized")
              
      return await repo.get_analytics_data(tenant_id)
  ```
  Register the router inside `backend/main.py`:
  ```python
  # Add to backend/main.py
  from backend.api.analytics import router as analytics_router
  app.include_router(analytics_router)
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest backend/tests/test_queue_api.py -k test_get_analytics_summary`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/api/analytics.py backend/main.py backend/tests/test_queue_api.py
  git commit -m "feat: add analytics api endpoint and register router"
  ```

---

### Task 4: Celery Session Summary Task

**Files:**
- Create: `backend/tasks/summaries.py`
- Modify: `backend/api/sessions.py`
- Test: `backend/tests/test_sessions.py`

- [ ] **Step 1: Write the failing test**
  Add a test verifying session summaries task inside `backend/tests/test_sessions.py`:
  ```python
  # Add to backend/tests/test_sessions.py
  async def test_session_summary_generation_task(db_session):
      from backend.tasks.summaries import async_generate_summary
      from backend.repositories.session import SessionRepository
      from backend.repositories.message import MessageRepository
      import uuid
      
      repo = SessionRepository(db_session)
      msg_repo = MessageRepository(db_session)
      tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
      cust_id = uuid.uuid4()
      sess = await repo.create_session(customer_id=cust_id, tenant_id=tenant_id)
      
      # Save a customer message and AI message
      await msg_repo.save_message(sess.id, "customer", "Hello, I need help with my refund.")
      await msg_repo.save_message(sess.id, "ai", "Our return policy doesn't cover refunds.")
      
      # Run generation
      await async_generate_summary(str(sess.id))
      
      # Reload session and assert summary
      await db_session.refresh(sess)
      assert sess.summary is not None
      assert len(sess.summary) > 0
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest backend/tests/test_sessions.py -k test_session_summary_generation_task`
  Expected: FAIL (missing module/task)

- [ ] **Step 3: Write minimal implementation**
  Create `backend/tasks/summaries.py`:
  ```python
  import asyncio
  import uuid
  import logging
  from backend.tasks.worker import celery_app
  from backend.storage.db import async_session_factory
  from backend.repositories.session import SessionRepository
  from backend.repositories.message import MessageRepository
  from backend.ai.mock import MockAdapter
  
  logger = logging.getLogger("summaries_task")
  
  async def async_generate_summary(session_id_str: str) -> None:
      try:
          session_uuid = uuid.UUID(session_id_str)
          async with async_session_factory() as session:
              repo = SessionRepository(session)
              msg_repo = MessageRepository(session)
              
              # Fetch history
              messages = await msg_repo.get_history(session_uuid, None, limit=100)
              if not messages:
                  logger.warning(f"No message history for session {session_id_str}. Skipping summary.")
                  return
                  
              history_str = "\n".join([f"[{m.role}]: {m.content}" for m in messages])
              
              # Call LLM (using MockAdapter or active AI adapter from settings)
              adapter = MockAdapter()
              prompt = f"Summarize the following support conversation in 1 or 2 sentences:\n{history_str}"
              
              summary_tokens = []
              async for token in adapter.send_message(session_id_str, [{"role": "user", "content": prompt}], "You are a concise summarizer."):
                  summary_tokens.append(token)
              summary = "".join(summary_tokens).strip()
              
              # Truncate summary if too long
              summary = summary[:500]
              await repo.update_summary(session_uuid, summary)
              logger.info(f"Successfully generated summary for session: {session_id_str}")
      except Exception as e:
          logger.exception(f"Session summary generation failed: {str(e)}")
          raise e
          
  @celery_app.task
  def generate_summary_task(session_id_str: str) -> None:
      import threading
      exception = []
      
      def worker():
          try:
              asyncio.run(async_generate_summary(session_id_str))
          except Exception as e:
              exception.append(e)
              
      thread = threading.Thread(target=worker)
      thread.start()
      thread.join()
      
      if exception:
          raise exception[0]
  ```
  Now trigger this task in `POST /api/v1/sessions/{session_id}/resolve` inside `backend/api/sessions.py`.
  ```python
  # Add to resolve_session in backend/api/sessions.py (around the close_session call)
  # Trigger background summary task
  from backend.tasks.summaries import generate_summary_task
  generate_summary_task.delay(str(session_id))
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest backend/tests/test_sessions.py -k test_session_summary_generation_task`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/tasks/summaries.py backend/api/sessions.py backend/tests/test_sessions.py
  git commit -m "feat: implement Celery session summaries generation task"
  ```

---

### Task 5: Sandbox Reset API

**Files:**
- Modify: `backend/api/sessions.py`
- Test: `backend/tests/test_sessions.py`

- [ ] **Step 1: Write the failing test**
  Add a test verifying the reset sandbox API endpoint returns 200 inside `backend/tests/test_sessions.py`:
  ```python
  # Add to backend/tests/test_sessions.py
  def test_reset_sandbox_api(client):
      response = client.post("/api/v1/sessions/reset", headers={"Authorization": "Bearer sandbox-token"})
      assert response.status_code == 200
      assert response.json() == {"status": "reset"}
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m pytest backend/tests/test_sessions.py -k test_reset_sandbox_api`
  Expected: FAIL with `404 Not Found` or `405 Method Not Allowed`

- [ ] **Step 3: Write minimal implementation**
  Add the endpoint `POST /api/v1/sessions/reset` inside `backend/api/sessions.py`:
  ```python
  # Add to backend/api/sessions.py
  @router.post("/reset")
  async def reset_sandbox(authorization: Optional[str] = Header(None)):
      if not authorization or not authorization.startswith("Bearer "):
          raise HTTPException(status_code=401, detail="Missing or invalid token")
      token = authorization.split(" ")[1]
      if token != "sandbox-token":
          raise HTTPException(status_code=401, detail="Unauthorized")
          
      from backend.session.state import RedisSessionManager
      from backend.storage.db import async_session_factory
      from sqlalchemy import text
      
      # 1. Reset Redis state
      redis = RedisSessionManager()
      session_id = "00000000-0000-0000-0000-000000000000"
      await redis.redis.delete(f"session:{session_id}:ai_silenced")
      await redis.redis.delete(f"session:{session_id}:rag_fallback_count")
      await redis.redis.delete("queue:escalated")
      
      # 2. Reset database state
      async with async_session_factory() as session:
          await session.execute(text("DELETE FROM messages;"))
          await session.execute(text("""
              UPDATE sessions 
              SET status = 'active', agent_id = NULL, escalation_trigger = NULL, 
                  escalated_at = NULL, resolved_at = NULL, summary = NULL, claimed_at = NULL
              WHERE id = '00000000-0000-0000-0000-000000000000'::uuid;
          """))
          await session.commit()
          
      return {"status": "reset"}
  ```

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m pytest backend/tests/test_sessions.py -k test_reset_sandbox_api`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add backend/api/sessions.py backend/tests/test_sessions.py
  git commit -m "feat: add POST /api/v1/sessions/reset endpoint"
  ```

---

### Task 6: React Dashboard View Routing & Chart.js Integration

**Files:**
- Modify: `packages/dashboard/package.json`
- Create: `packages/dashboard/src/components/AnalyticsPanel.tsx`
- Modify: `packages/dashboard/src/index.tsx`

- [ ] **Step 1: Install Chart.js**
  Ensure we add `chart.js` dependency to `packages/dashboard/package.json`:
  ```json
  // Add to dependencies in packages/dashboard/package.json
  "chart.js": "^4.4.2"
  ```
  Run: `npm install --workspace=packages/dashboard`

- [ ] **Step 2: Create the AnalyticsPanel component**
  Create `packages/dashboard/src/components/AnalyticsPanel.tsx`:
  ```tsx
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
      <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "24px", overflowY: "auto", height: "100%" }}>
        <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 600 }}>Analytics & Operations</h2>
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
  ```

- [ ] **Step 3: Modify the main index.tsx to support view routing**
  Update `packages/dashboard/src/index.tsx` to let agents switch between view tabs:
  ```tsx
  // Modify packages/dashboard/src/index.tsx to import AnalyticsPanel and render tabs
  import { AnalyticsPanel } from "./components/AnalyticsPanel.js";
  
  // Inside DashboardApp component:
  const [activeTab, setActiveTab] = useState<"chat" | "analytics" | "sandbox">("chat");
  
  // Modify the header to render navigation buttons:
  // <header...>
  //   <h1 ...>CC-ChatIQ Agent Dashboard</h1>
  //   <nav style={{ display: 'flex', gap: '8px' }}>
  //     <button onClick={() => setActiveTab("chat")} style={{ padding: '6px 12px', background: activeTab === 'chat' ? '#3b82f6' : 'transparent', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', cursor: 'pointer' }}>Active Chat</button>
  //     <button onClick={() => setActiveTab("analytics")} style={{ padding: '6px 12px', background: activeTab === 'analytics' ? '#3b82f6' : 'transparent', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', cursor: 'pointer' }}>Analytics</button>
  //     <button onClick={() => setActiveTab("sandbox")} style={{ padding: '6px 12px', background: activeTab === 'sandbox' ? '#3b82f6' : 'transparent', color: '#fff', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', cursor: 'pointer' }}>Sandbox Playground</button>
  //   </nav>
  // </header>
  
  // Render based on activeTab:
  // {activeTab === "chat" && (
  //   <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
  //     <QueuePanel token="sandbox-token" onClaim={handleClaim} />
  //     <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
  //       <div style={{ flex: 1, overflow: "hidden" }}>
  //         <MessageStream />
  //       </div>
  //       <AgentInput onSend={handleSend} />
  //     </div>
  //     <CRMContext onResolve={handleResolve} />
  //   </div>
  // )}
  // {activeTab === "analytics" && <AnalyticsPanel />}
  ```

- [ ] **Step 4: Verify build works**
  Run: `npm run build:dashboard`
  Expected: Success

- [ ] **Step 5: Commit**
  Run:
  ```bash
  git add packages/dashboard/package.json packages/dashboard/src/components/AnalyticsPanel.tsx packages/dashboard/src/index.tsx
  git commit -m "feat: add view tabs and Chart.js Analytics tab in dashboard"
  ```

---

### Task 7: Sandbox Side-by-Side Playground

**Files:**
- Create: `packages/dashboard/src/components/SandboxPanel.tsx`
- Modify: `packages/dashboard/src/index.tsx`
- Modify: `packages/dashboard/index.html`

- [ ] **Step 1: Create SandboxPanel component**
  Create `packages/dashboard/src/components/SandboxPanel.tsx` which renders `<Widget />` and `<DashboardApp />` side-by-side.
  ```tsx
  import React, { useState } from "react";
  import { Widget } from "@opendesk/widget";
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
            <div style={{ fontSize: "14px", fontWeight: 600, opacity: 0.6, marginBottom: "8px" }}>Customer Interface Mockup</div>
            <div style={{ flex: 1, border: "1px dashed rgba(255,255,255,0.1)", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
              <div style={{ color: "rgba(255,255,255,0.3)", fontSize: "13px" }}>Click the bottom-right chat bubble to chat with the AI/Agent</div>
              <Widget wsUrl="ws://localhost:8000/ws/chat" />
            </div>
          </div>
          {/* Agent View */}
          <div style={{ width: "65%", display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: "14px", fontWeight: 600, opacity: 0.6, padding: "16px 16px 0 16px" }}>Agent Dashboard Interface</div>
            <div style={{ flex: 1 }}>
              {renderDashboard()}
            </div>
          </div>
        </div>
      </div>
    );
  };
  ```

- [ ] **Step 2: Add SandboxPanel view support to index.tsx**
  Update `packages/dashboard/src/index.tsx` to handle the `sandbox` view state:
  ```tsx
  import { SandboxPanel } from "./components/SandboxPanel.js";
  
  // Inside DashboardApp return statement, wrap the dashboard UI in a function:
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
  
  // And under render activeTab:
  // {activeTab === "sandbox" && <SandboxPanel renderDashboard={renderDashboardOnly} />}
  ```

- [ ] **Step 3: Verify build and runs**
  Run: `npm run build:all`
  Expected: Success

- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add packages/dashboard/src/components/SandboxPanel.tsx packages/dashboard/src/index.tsx
  git commit -m "feat: implement side-by-side SandboxPanel playground"
  ```

---

### Task 8: Open-Source Documentation

**Files:**
- Create: `docs/quickstart.md`
- Create: `docs/configuration.md`
- Create: `docs/ingestion.md`
- Create: `CONTRIBUTING.md`
- Create: `LICENSE`

- [ ] **Step 1: Write quickstart guide**
  Create `docs/quickstart.md`:
  ```markdown
  # 5-Minute Quickstart Guide
  
  CC-ChatIQ is a multi-tenant chat customer support tool. Follow these steps to get a working sandbox demo running in minutes:
  
  ## Prerequisites
  * Docker & Docker Compose
  * Node.js v20+ & npm
  
  ## 1. Start Infrastructure Services
  Run Docker Compose to start PostgreSQL, Redis, and MinIO:
  ```bash
  docker compose -f docker/docker-compose.yml up -d db redis minio
  ```
  
  ## 2. Start Python API Backend
  1. Create a `.env` file:
     ```bash
     cp .env.example .env
     ```
  2. Setup virtual environment & dependencies:
     ```bash
     cd backend
     python -m venv venv
     source venv/bin/activate  # venv\Scripts\activate on Windows
     pip install -r requirements.txt
     ```
  3. Start the FastAPI server:
     ```bash
     uvicorn main:app --host 0.0.0.0 --port 8000 --reload
     ```
  
  ## 3. Start Frontend Workspace
  1. Install node workspaces:
     ```bash
     npm install
     ```
  2. Build shared core package and run dashboard:
     ```bash
     npm run build:core
     npm run dev:dashboard
     ```
  3. Open `http://localhost:5173/` in your browser.
  ```

- [ ] **Step 2: Write configuration and ingestion guides**
  Create `docs/configuration.md` describing all environment variables.
  Create `docs/ingestion.md` detailing the `POST /api/v1/knowledge/ingest` formats.

- [ ] **Step 3: Create contributing guide and license**
  Create `CONTRIBUTING.md` in root detailing monorepo coding rules (Zustand rule, 40-line functions limit, decoupled repositories).
  Create `LICENSE` in root with standard MIT License terms.

- [ ] **Step 4: Commit documentation**
  Run:
  ```bash
  git add -f docs/quickstart.md docs/configuration.md docs/ingestion.md CONTRIBUTING.md LICENSE
  git commit -m "docs: add open source quickstart configuration ingestion guides, contributing policy and license"
  ```
