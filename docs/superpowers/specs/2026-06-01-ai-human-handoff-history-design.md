# Design Spec: AI-Human Handoff Session History Retrieval

## Goal
Resolve the issue where the agent dashboard is unable to view the historical conversation between a customer and the AI bot during and after handoff. Specifically, authenticate and authorize the agent dashboard's requests to retrieve a session's history while enforcing strict tenant isolation boundaries.

## Proposed Design
We will modify the session history retrieval endpoint `GET /api/v1/sessions/{session_id}` in `backend/api/sessions.py` to support agent authorization:

1. **Role Identification**:
   - Determine if the caller is the customer or an agent.
   - If the request has `LOCAL_TESTING = True` and the token is `"sandbox-token"`, treat the caller as an authorized agent.
   - Otherwise, decode the JWT token. If `claims.sub == session_id`, the caller is the customer. If `claims.sub != session_id`, the caller is an agent.

2. **Tenant Resolution**:
   - If the caller is the customer, use the `tenant_id` from their token claims.
   - If the caller is an agent:
     - Query the database to retrieve the session object by `session_id`.
     - Extract `tenant_id` from the retrieved session.
     - If the agent's token includes a `tenant_id` claim, verify that it matches the session's `tenant_id` to enforce strict tenant isolation. If they do not match, return a `403 Forbidden` response.

3. **History Retrieval**:
   - Query the message history using `MessageRepository.get_history` with the verified `tenant_id`.

## Verification Plan

### Automated Tests
- Create unit tests in `backend/tests/test_sessions.py` to cover:
  - Retrieval of session history by the customer.
  - Retrieval of session history by the agent in local testing mode using `"sandbox-token"`.
  - Retrieval of session history by an authorized agent in non-local environments.
  - Rejection of retrieval requests by unauthorized agents or agents with non-matching tenant IDs.

### Manual Verification
- Verify that claiming an escalated session in the dashboard correctly loads the historical messages from the backend.
