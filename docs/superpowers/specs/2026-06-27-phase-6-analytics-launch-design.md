# Phase 6: Analytics & Launch Design Spec

This document details the architecture, data models, endpoints, background tasks, UI dashboard tabs, sandboxed demo environment, and onboarding documents for the final launch phase.

---

## 1. Database Schema Updates (`backend/storage/schema.py`)

We will extend the `sessions` table (`SessionModel`) to include two new columns:
* `summary` (Text, nullable=True): Stores the 1-2 sentence AI-generated conversation summary.
* `claimed_at` (DateTime(timezone=True), nullable=True): Stores the timestamp when an agent first claimed the session.

```python
class SessionModel(Base):
    __tablename__ = "sessions"
    # ... existing columns ...
    summary = Column(Text, nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
```

---

## 2. Session Repository Updates (`backend/repositories/session.py`)

We will add or update the following methods in the concrete `SessionRepository` implementation:
* `claim_session(self, session_id: UUID, agent_id: UUID)`:
  Updates the session with `agent_id`, sets `status = 'active'`, and updates `claimed_at = func.now()`.
* `update_summary(self, session_id: UUID, summary: str)`:
  Updates `summary = summary` for the given session ID.
* `get_analytics_data(self)`:
  Computes aggregated metrics from PostgreSQL:
  * Total session count.
  * Escalation count and rates grouped by `escalation_trigger` (e.g. `calmiq`, `user_request`, `keyword_trigger`, `manual_transfer`).
  * Average wait time: `AVG(claimed_at - escalated_at)` for sessions that transitioned to human agents.
  * RAG fallback metrics: count of sessions with `escalation_trigger = 'rag_fallback'`.

---

## 3. Celery Summaries Task (`backend/tasks/summaries.py`)

When a session is marked as resolved, a Celery task is triggered to summarize the conversation:
* **Handler (`async_generate_summary`)**:
  * Loads session history using `MessageRepository.get_history()`.
  * Formats history: `[Role]: Content`.
  * Calls the active AI LLM provider using the `AIProviderAdapter` protocol.
  * Instructs the LLM via system prompt: *"Summarize the following support conversation in 1 or 2 sentences."*
  * Updates the session record via `SessionRepository.update_summary()`.
* **Celery task wrapper (`generate_summary_task`)**:
  * Runs the async handler inside `asyncio.run()` in a spawned thread (matching the established pattern in `ingest_document_task`).

---

## 4. API Endpoints

### 4.1 Analytics API (`backend/api/analytics.py`)
* `GET /api/v1/analytics/summary`
* **Authorization**: Bearer JWT token (with role = `agent` or `admin`) or `"Bearer sandbox-token"` for local testing.
* **Response**:
  ```json
  {
    "total_sessions": 42,
    "escalations_by_trigger": {
      "calmiq": 12,
      "user_request": 15,
      "keyword_trigger": 10,
      "manual_transfer": 5
    },
    "average_wait_time_seconds": 182.5,
    "rag_fallback_count": 8
  }
  ```

### 4.2 Reset Sandbox API (`backend/api/sessions.py` or new endpoint)
* `POST /api/v1/sessions/reset`
* **Response**: `{ "status": "reset" }`
* **Behavior**:
  * Deletes messages from the database.
  * Resets the default session (`00000000-0000-0000-0000-000000000000`) status to `active`, clears `agent_id`, `escalation_trigger`, `escalated_at`, `resolved_at`, and `summary`.
  * Clears Redis keys: `session:00000000-0000-0000-0000-000000000000:ai_silenced`, `session:00000000-0000-0000-0000-000000000000:rag_fallback_count`, and `queue:escalated`.

---

## 5. Frontend Dashboard & Sandbox Tab (`packages/dashboard/src/index.tsx`)

### 5.1 Navigation View Selector
A header button group switches the main container between:
* `chat` (Active conversation panels)
* `analytics` (Analytics charts)
* `sandbox` (Side-by-side demo layout)

### 5.2 Analytics Dashboard View (`packages/dashboard/src/components/AnalyticsPanel.tsx`)
* Fetches data from `/api/v1/analytics/summary`.
* Installs and uses `chart.js` for charts:
  * **Line Chart**: Volume of sessions.
  * **Doughnut Chart**: Distribution of escalation triggers.
  * **Stat Cards**: Displaying "Average Wait Time" (formatted in minutes and seconds) and "RAG Fallback Count".

### 5.3 Interactive Sandbox view (`packages/dashboard/src/components/SandboxPanel.tsx`)
* **Layout**: Left panel displays the customer chat widget, right panel displays the agent dashboard.
* **Control**: A header bar contains a "Reset Sandbox" button. Clicking this triggers the reset endpoint and reloads the views.

---

## 6. Open Source Package & Guides

* **`LICENSE`**: Standard MIT License text in root.
* **`CONTRIBUTING.md`**: Guide outlining the monorepo architecture, coding standards (no direct SQLAlchemy imports in API, Zustand rule, 40-line function limits).
* **`/docs/quickstart.md`**: 5-minute setup guide to boot the stack with Docker Compose and test using `MockAdapter`.
* **`/docs/configuration.md`**: Reference of all environment variables.
* **`/docs/ingestion.md`**: Guide for uploading and chunking PDFs/txt/URLs.
