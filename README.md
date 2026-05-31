# CC-ChatIQ — Omni-Channel Customer Support Platform

CC-ChatIQ is a modern, decoupled, multi-tenant customer support platform designed for real-time customer and assistant engagement, robust persistence, and high-performance LLM-driven support capabilities.

---

## 🚀 Key Features

*   **Real-Time Bi-directional Communication:** Employs high-throughput WebSocket streams for live messaging with built-in heartbeat (`ping`/`pong`) mechanisms.
*   **Resilient Connectivity:** Client-side custom hook (`useWebSocket`) featuring exponential backoff reconnection with random jitter and offline message queuing.
*   **Transactional Reconnection Order:** Eliminates race conditions on reconnect by synchronizing historical conversation data via REST before flushing offline buffers.
*   **Stateless JWT Security Handshake:** Secures all communication channels with timezone-aware JWT tokens encapsulating role and strict tenant mapping.
*   **Decoupled Repository Pattern:** Implements database-agnostic repository interfaces. Core API logic never imports SQLAlchemy or database drivers directly.
*   **Custom Floating Support Widget:** Memoized React floating widget panel with glassmorphism aesthetics, slide animations, and glowing connection status LEDs.
*   **Dockerized Infrastructure Orchestration:** Multi-container configuration bootstrapping PostgreSQL (with pgvector), Redis, MinIO, FastAPI, and Celery worker.

---

## 📂 Monorepo Structure

CC-ChatIQ is structured as a TypeScript ESM monorepo:

```
├── backend/                  # FastAPI Python backend server
│   ├── api/                  # HTTP REST endpoints (session initialization)
│   ├── ws/                   # WebSocket endpoints (chat routing and echo loops)
│   ├── storage/              # Database Async engines, sessions, and schemas
│   ├── repositories/         # Decoupled multi-tenant base and concrete repositories
│   ├── session/              # Redis session state manager
│   ├── ai/                   # Modular LLM adapters (abstract and mock implementations)
│   └── tests/                # Comprehensive test suites for API, database, and sockets
│
├── packages/                 # Front-end packages workspace
│   ├── core/                 # Shared store logic (Zustand message and session stores, useWebSocket)
│   ├── widget/               # Floating React support widget bubble and visual Panels
│   └── dashboard/            # Agent workspace console
│
├── docker/                   # Docker environment files and volume setups
└── README.md                 # Project roadmap and architecture guide
```

---

## 🛠️ Tech Stack

*   **Backend:** Python 3.11, FastAPI 0.111, Uvicorn, SQLAlchemy 2.0, Asyncpg, Pytest, Python-Jose.
*   **Caching & State:** Redis 7 (Async Redis CLI client), Zustand 4.5.2.
*   **Frontend:** React 18.3, TypeScript 5.4, Vite 5.2.
*   **Infrastructure:** PostgreSQL 16 (Pgvector), MinIO, Docker Compose.

---

## 🚀 Getting Started

### Prerequisites
*   Docker & Docker Compose
*   Node.js v20+ & npm

### Infrastructure Setup
Spin up the PostgreSQL, Redis, and MinIO instances via Docker:
```bash
docker compose -f docker/docker-compose.yml up -d db redis minio
```

### Backend Startup
1. Configure environment variables in a `.env` file (see `.env.example` for reference).
2. Install dependencies and run the FastAPI server:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
3. Run the backend unit tests to verify:
```bash
pytest
```

### Frontend Workspace Setup
1. From the monorepo root directory, install all workspace packages and links:
```bash
npm install
```
2. Compile the shared `core` package:
```bash
npm run build:core
```
3. Boot the widget development environment:
```bash
npm run dev:widget
```
