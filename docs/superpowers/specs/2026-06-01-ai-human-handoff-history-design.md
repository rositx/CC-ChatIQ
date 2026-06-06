# Design Spec: AI-Human Handoff Session History & Sentiment Matrix

## Goal
1. Resolve the issue where the agent dashboard is unable to view the historical conversation between a customer and the AI bot during and after handoff. Specifically, authenticate and authorize the agent dashboard's requests to retrieve a session's history while enforcing strict tenant isolation boundaries.
2. Integrate and display the "Customer Sentiment Matrix" (frustration scoring) inside the agent dashboard's CRM sidebar.

## Proposed Design

### 1. Session History Retrieval & Role-Based Authorization
We will modify the session history retrieval endpoint `GET /api/v1/sessions/{session_id}` in `backend/api/sessions.py` to support agent authorization:
- **Role Identification**:
  - Determine if the caller is the customer or an agent.
  - If the request has `LOCAL_TESTING = True` and the token is `"sandbox-token"`, treat the caller as an authorized agent.
  - Otherwise, decode the JWT token. If `claims.sub == session_id`, the caller is the customer. If `claims.sub != session_id`, the caller is an agent.
- **Tenant Resolution**:
  - If the caller is the customer, use the `tenant_id` from their token claims.
  - If the caller is an agent:
    - Query the database to retrieve the session object by `session_id`.
    - Extract `tenant_id` from the retrieved session.
    - If the agent's token includes a `tenant_id` claim, verify that it matches the session's `tenant_id` to enforce strict tenant isolation. If they do not match, return a `403 Forbidden` response.
- **History Retrieval**:
  - Query the message history using `MessageRepository.get_history` with the verified `tenant_id`.

### 2. Session Metadata Endpoint
Add a new endpoint `GET /api/v1/sessions/{session_id}/metadata` in `backend/api/sessions.py` to retrieve session metadata (including `peak_score` / frustration score) for the agent dashboard. This endpoint will enforce the exact same role-based tenant isolation rules as the history retrieval endpoint.

### 3. Database & Webhook Frustration Score Updates
- Update the CalmIQ webhook endpoint `POST /api/v1/webhooks/calmiq` in `backend/api/webhooks.py` to support optional `score` and `frustration_score` fields in the incoming payload.
- Implement `update_peak_score` in `SessionRepository` to persist the frustration score into the session's `peak_score` column.
- In `POST /api/v1/webhooks/calmiq`, extract the score and persist it using `SessionRepository.update_peak_score`.

### 4. Agent Dashboard UI Integration (Sentiment Matrix)
- Update `packages/dashboard/src/components/CRMContext.tsx` to:
  - Fetch `/api/v1/sessions/{session_id}/metadata` when `activeSessionId` is set.
  - Display the customer's sentiment metrics/frustration score as a premium visual indicator (e.g. Calm, Frustrated, or Highly Frustrated with color coding based on `peak_score`).

## Verification Plan

### Automated Tests
- Create unit tests in `backend/tests/test_sessions.py` to cover:
  - Retrieval of session history by the customer.
  - Retrieval of session history by the agent in local testing mode using `"sandbox-token"`.
  - Retrieval of session history by an authorized agent in non-local environments.
  - Rejection of retrieval requests by unauthorized agents or agents with non-matching tenant IDs.
  - Retrieval of session metadata using `GET /api/v1/sessions/{session_id}/metadata`.
  - Storing and updating of `peak_score` via `POST /api/v1/webhooks/calmiq` webhook.

### Manual Verification
- Verify that claiming an escalated session in the dashboard correctly loads the historical messages from the backend.
- Verify that selecting an active session displays the correct real-time frustration/sentiment rating in the customer context sidebar.

