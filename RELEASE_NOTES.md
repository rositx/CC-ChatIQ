# OpenDesk Omni-Channel Platform Release Notes

This document highlights the major features and capabilities established during Phase 0 (Foundation) and Phase 1 (Core Chat) of the OpenDesk project.

---

## 🚀 Phase 1: Core Chat Features

### 1. Real-Time Bidirectional WebSocket Routing
- **Handshake Validation:** Implemented stateless secure authentication query parameters (`/ws/chat/{session_id}?token=JWT`). Handshake resolves JWT, decodes tenant context, and verifies session match, safely terminating invalid connections with exit code `4001`.
- **Frame Transport:** Handles bidirectional JSON-based frame channels supporting standard operations:
  - `ping` / `pong` heartbeat signals to maintain persistent live connections.
  - `message` payload structure wrapping customer, agent, and AI communications.
- **Helper Modularization:** Reorganized route handlers under `backend/ws/chat.py` into cohesive, focused handlers under 40 lines of code.

### 2. Concrete Multi-Tenant Repositories & Scoped DB Sessions
- **Message Repository:** PERSISTS active customer and agent messages inside `backend/repositories/message.py` with transactional rollback encapsulation.
- **Tenant Isolation:** Enforces strict multi-tenant boundary checks on history retrieval (`get_history`) by joining with `SessionModel` and matching `tenant_id`.

### 3. Provider-Agnostic AI Adapter Interface
- **AI Interface:** Created abstract base `AIProviderAdapter` interface in `backend/ai/base.py` enabling modular swaps of LLM engines.
- **Mock Token Streamer:** Created concrete offline `MockAdapter` yielding deterministic token streaming asynchronously (`await asyncio.sleep(0.02)`) without blocking the event loop.

### 4. Custom ESM Client Libraries (`opendesk-core`)
- **Global Zustand Stores:** Deployed `useSessionStore` and `useMessageStore` to manage shared client states with zero React Context API boundaries.
- **Resilient useWebSocket Hook:**
  - Implements randomized exponential backoff with +/- 20% jitter.
  - Deploys **Transactional Reconnection Order Flow**: on successful handshake, fetches history via REST, merges and deduplicates chronologically, and only then flushes in-memory offline message queues.
  - Structured with fully type-safe signatures and zero `any` keywords.

### 5. Floating Visual Web Widget (`opendesk-widget`)
- **High Performance:** Deploys visual bubble lists utilizing `React.memo` to optimize rendering speed.
- **Rich Aesthetic:** Glassmorphism overlay panels, subtle slide animations, and glowing circular toggles.
- **Visual LED Beacons:** Renders blinking indicator beacons depicting colored states corresponding to socket connectivity.

---

## 🛠️ Phase 0: Foundation Architecture

### 1. Monorepo Setup & ESM Workspaces
- Established workspaces under `/packages` (`core`, `widget`, `dashboard`, `mobile`) sharing inherited TS compile configurations.
- Formatted as pure ESM output mapping (`"type": "module"`) to enable Rollup bundling.

### 2. Multi-Container Orchestration (Docker)
- Standardized compose configs bootstrapping `pgvector:v0.5.1-pg16`, `redis:7-alpine`, `minio/minio`, FastAPI, and Celery worker services.

### 3. Token Security & Async Database Models
- **JWT Cryptography:** Decoupled security constants inside `backend/config.py` and deployed timezone-aware JWT helper functions withUUID serialization safety.
- **Async Database Pooling:** Created async engine pools in `backend/storage/db.py` yielding scoped database connections.
- **Colleague Collision Prevention:** Decoupled database schema namespaces by mapping the JSONB column metadata to model property `metadata_` to resolve SQLAlchemy declarative base collisions.
- **Agnostic FastAPI REST Routes:** Configured lifecycleLifespan startup creators and agnostic uvicorn endpoints.
