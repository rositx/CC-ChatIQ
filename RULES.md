# CC-ChatIQ — Non-Negotiable Development Rules

> This file governs all code generation for the CC-ChatIQ project.
> Every rule here is mandatory. No exceptions without explicit developer approval.

---

## 1. No Repetitive Code — Ever

- Before writing any new function, search the codebase for existing functions that do the same or similar thing
- If a similar function exists — extend or refactor it, never duplicate it
- If two functions share more than 5 lines of logic — extract the shared logic into a utility function
- Shared frontend logic lives in `packages/core` — if you find yourself writing the same hook or utility twice in any package, it belongs there
- Shared backend logic lives in `backend/utils/` — never inline something that already exists there
- DRY is not a preference here — it is a hard rule

**Before creating any new function ask:**
> "Does something like this already exist in this package or in `packages/core` / `backend/utils/`?"
> If yes — use it, extend it, or refactor it. Never write a parallel version.

---

## 2. Clean Code Standards

- **One responsibility per function** — if a function does two things, split it
- **One responsibility per file** — if a file handles two concerns, split it
- **Max function length: 40 lines** — if it's longer, break it down
- **Max file length: 200 lines** — if it's longer, split it by responsibility
- No commented-out dead code — delete it
- No unused imports — remove them immediately
- No hardcoded magic numbers, strings, model names, or URLs — all constants live in `config.py` (backend) or `packages/core/src/constants.ts` (frontend)
- All thresholds, limits, provider names, score weights, time windows, and API paths are defined in config, never inline

---

## 3. File Structure — Follow This Exactly

```
cc-chatiq/
├── backend/
│   ├── config.py                        # All constants, thresholds, provider names — nothing else
│   ├── main.py                          # FastAPI app init + router registration only
│   ├── api/
│   │   ├── sessions.py                  # Session CRUD endpoints only
│   │   ├── knowledge.py                 # Knowledge base ingestion + management endpoints only
│   │   ├── queue.py                     # Agent queue claim/list endpoints only
│   │   ├── analytics.py                 # Analytics summary endpoints only
│   │   └── webhooks.py                  # Inbound CalmIQ webhook endpoint only
│   ├── ws/
│   │   ├── chat.py                      # Customer-facing WebSocket handler only
│   │   └── agent.py                     # Agent dashboard WebSocket handler only
│   ├── rag/
│   │   ├── pipeline.py                  # Orchestrates retrieve → inject → generate only
│   │   ├── retriever.py                 # pgvector similarity search only
│   │   ├── ingestion.py                 # Document chunking + embedding + storage only
│   │   └── prompt.py                    # RAG prompt template assembly only
│   ├── ai/
│   │   ├── base.py                      # AIAdapter abstract base class only
│   │   ├── anthropic.py                 # AnthropicAdapter implementation only
│   │   ├── openai.py                    # OpenAIAdapter implementation only
│   │   ├── azure.py                     # AzureOpenAIAdapter implementation only
│   │   └── mock.py                      # MockAdapter for testing — no API key required
│   ├── handoff/
│   │   ├── triggers.py                  # All escalation trigger detection only
│   │   ├── executor.py                  # Executes handoff sequence — silences AI, pushes queue
│   │   └── queue_manager.py             # Agent queue depth check + WebSocket push only
│   ├── scoring/
│   │   └── hook.py                      # Async CalmIQ webhook call only (BackgroundTask)
│   ├── repositories/
│   │   ├── base.py                      # Repository abstract interfaces only
│   │   ├── customer.py                  # CustomerRepository implementation only
│   │   ├── session.py                   # SessionRepository implementation only
│   │   ├── message.py                   # MessageRepository implementation only
│   │   ├── agent.py                     # AgentRepository implementation only
│   │   └── knowledge.py                 # KnowledgeRepository + pgvector queries only
│   ├── session/
│   │   ├── state.py                     # Redis read/write for session state only
│   │   └── schema.py                    # Session Pydantic schemas only
│   ├── storage/
│   │   ├── db.py                        # PostgreSQL async engine + session factory only
│   │   └── schema.py                    # SQLAlchemy table definitions only
│   ├── utils/
│   │   ├── embedder.py                  # Single embedding utility used by all RAG modules
│   │   ├── text.py                      # Text cleaning, chunking, keyword detection
│   │   ├── jwt.py                       # JWT sign/verify helpers only
│   │   └── pagination.py                # Shared pagination helpers only
│   ├── tasks/
│   │   ├── worker.py                    # Celery app init only
│   │   ├── ingestion.py                 # Async knowledge ingestion Celery tasks only
│   │   └── summaries.py                 # Session summary generation Celery tasks only
│   └── tests/
│       ├── test_rag.py
│       ├── test_handoff.py
│       ├── test_sessions.py
│       ├── test_repositories.py
│       ├── test_ai_adapters.py
│       └── test_webhooks.py
│
├── packages/
│   ├── core/                            # Shared logic — imported by widget, dashboard, mobile
│   │   └── src/
│   │       ├── constants.ts             # All shared frontend constants only
│   │       ├── types.ts                 # All shared TypeScript types + interfaces only
│   │       ├── hooks/
│   │       │   ├── useWebSocket.ts      # Single WebSocket client hook — used by ALL packages
│   │       │   ├── useSession.ts        # Session create/resume logic
│   │       │   └── useMessages.ts       # Message list state + append logic
│   │       └── stores/
│   │           ├── sessionStore.ts      # Zustand session atom
│   │           └── messageStore.ts      # Zustand message list atom
│   │
│   ├── widget/                          # Web chat widget — React, ships as ESM + UMD
│   │   └── src/
│   │       ├── Widget.tsx               # Root component + config init only
│   │       ├── components/
│   │       │   ├── ChatPanel.tsx        # Message list + input panel
│   │       │   ├── MessageBubble.tsx    # Single message render (AI / agent / customer)
│   │       │   ├── TypingIndicator.tsx  # Typing animation only
│   │       │   └── HandoffBanner.tsx    # Escalation status UI only
│   │       └── stores/
│   │           └── widgetStore.ts       # Widget-local Zustand state (open/closed, theme)
│   │
│   ├── dashboard/                       # React agent dashboard — Vite SPA
│   │   └── src/
│   │       ├── App.tsx                  # Route definitions only
│   │       ├── pages/
│   │       │   ├── Queue.tsx            # Escalation queue page only
│   │       │   ├── ActiveChat.tsx       # Active session chat page only
│   │       │   └── Analytics.tsx        # Analytics dashboard page only
│   │       ├── components/
│   │       │   ├── QueueItem.tsx        # Single queue entry card
│   │       │   ├── MessageStream.tsx    # Memoized streaming message renderer
│   │       │   ├── CustomerContext.tsx  # Right-panel customer metadata
│   │       │   └── AgentInput.tsx       # Agent message input + quick replies
│   │       └── stores/
│   │           ├── queueStore.ts        # Escalation queue Zustand state
│   │           └── agentStore.ts        # Agent status + active session Zustand state
│   │
│   └── mobile/                          # React Native SDK — Expo
│       └── src/
│           ├── SupportChat.tsx          # Exported root component
│           ├── useSupportChat.ts        # Exported hook
│           └── components/
│               ├── MobileChatPanel.tsx
│               └── MobileHandoffBanner.tsx
│
├── docker/
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
└── docs/
```

**Rules for the structure:**
- Never put RAG logic in the API layer — the API calls `rag/pipeline.py`, it does not build prompts itself
- Never put handoff logic in the WebSocket handlers — handlers call `handoff/executor.py`, they do not execute handoff themselves
- Never put session state logic outside `session/state.py` (backend) or `packages/core/stores/` (frontend)
- Never open a Redis connection outside `session/state.py`
- Never open a PostgreSQL connection outside `storage/db.py`
- Never call an embedding API outside `utils/embedder.py`
- Never implement a WebSocket client outside `packages/core/hooks/useWebSocket.ts`
- `packages/core` is imported by widget, dashboard, and mobile — nothing in core imports from those packages
- If a new file is needed that doesn't fit this structure — ask before creating it

---

## 4. Check Before You Create

This is the most important rule operationally.

**Every time before writing a new function or component:**

1. Search for the function name or similar names across the monorepo
2. Search for the core logic (e.g., "WebSocket reconnect", "chunk split", "similarity search")
3. Check `packages/core` first for frontend — it is the first home for any reusable hook or utility
4. Check `backend/utils/` first for backend — it is the first home for any reusable helper
5. Check if an existing function can be extended with a parameter instead of duplicated

**Specific cases to watch:**
- WebSocket connection logic lives in ONE place: `packages/core/hooks/useWebSocket.ts` — never reimplement it in widget, dashboard, or mobile
- Embedding calls happen in ONE place: `backend/utils/embedder.py` — never inline an embedding call in the RAG pipeline or ingestion tasks
- Text chunking and cleaning happens in ONE place: `backend/utils/text.py` — never rewrite chunking logic in the ingestion task
- JWT sign/verify happens in ONE place: `backend/utils/jwt.py` — never inline JWT logic in a route handler
- All threshold and config values read from ONE place: `config.py` (backend) or `constants.ts` (frontend) — never hardcode values inline
- Redis connections opened in ONE place: `session/state.py` — no exceptions
- PostgreSQL connections opened in ONE place: `storage/db.py` — no exceptions
- Handoff trigger evaluation happens in ONE place: `handoff/triggers.py` — no other file decides "should we escalate"
- Handoff execution happens in ONE place: `handoff/executor.py` — no other file silences the AI or pushes the queue

---

## 5. Configuration — All of It Lives in config.py / constants.ts

### Backend — config.py

```python
# AI provider
AI_PROVIDER = "anthropic"                        # anthropic | openai | azure | mock
AI_MODEL_ANTHROPIC = "claude-sonnet-4-20250514"
AI_MODEL_OPENAI = "gpt-4o"
AI_TEMPERATURE = 0.3
AI_MAX_TOKENS = 1024

# Embedding
EMBEDDING_PROVIDER = "openai"                    # openai | cohere | local
EMBEDDING_MODEL_OPENAI = "text-embedding-3-small"
EMBEDDING_MODEL_LOCAL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 1536

# RAG retrieval
RAG_TOP_K = 5
RAG_MIN_SIMILARITY = 0.72
RAG_MAX_CONTEXT_TOKENS = 2000
RAG_CHUNK_SIZE = 512
RAG_CHUNK_OVERLAP = 64
KNOWLEDGE_STALE_DAYS = 90
RAG_FALLBACK_ESCALATION_THRESHOLD = 3           # escalate after N fallback phrases in one session

# Handoff
KEYWORD_TRIGGER_LIST = ["cancel", "refund", "manager", "human", "representative", "useless", "broken"]
AGENT_QUEUE_MAX_DEPTH = 50

# Session
SESSION_TTL_SECONDS = 86400

# CalmIQ integration
CALMIQ_WEBHOOK_URL = ""                          # empty string = integration disabled
CALMIQ_SECRET_HEADER = "X-CalmIQ-Secret"

# Rate limiting
RATE_LIMIT_MESSAGES_PER_MINUTE = 30
RATE_LIMIT_SESSIONS_PER_IP = 10
```

### Frontend — packages/core/src/constants.ts

```typescript
export const WS_RECONNECT_BASE_MS = 1000;
export const WS_RECONNECT_MAX_MS = 30000;
export const WS_HEARTBEAT_INTERVAL_MS = 25000;
export const MESSAGE_HISTORY_PAGE_SIZE = 50;
export const QUEUE_POLL_INTERVAL_MS = 0;         // 0 = WebSocket push only, no polling
export const TYPING_INDICATOR_TIMEOUT_MS = 3000;
export const MAX_FILE_SIZE_BYTES = 10_485_760;   // 10MB
export const ACCEPTED_FILE_TYPES = ["image/jpeg", "image/png", "application/pdf"];
```

If a constant does not exist in config yet — add it there first, then use it. Never the other way around.

---

## 6. AI Adapter Rules

- Every AI provider is an implementation of `AIAdapter` (defined in `ai/base.py`) — no provider-specific code outside its own file
- The active adapter is injected at application startup via the `AI_PROVIDER` environment variable — never with if/else in service code
- Every adapter must implement: `send_message(session_id, messages, system_prompt) -> AsyncGenerator[str, None]` (streaming)
- The `MockAdapter` must return deterministic responses — it must never make a network call
- If a new provider adapter is added, it must pass the same test suite as all existing adapters — no special cases in tests

**Adapter rule check:**
> "Does this code know which LLM provider is active?"
> If yes — it does not belong in service code. Move it to the adapter.

---

## 7. RAG Pipeline Rules

- The pipeline in `rag/pipeline.py` has one job: call retriever → call prompt builder → call AI adapter. Nothing else.
- Retrieval logic lives only in `rag/retriever.py` — the pipeline never builds a pgvector query directly
- Prompt assembly lives only in `rag/prompt.py` — the pipeline never concatenates strings to build a system prompt
- Ingestion (chunking + embedding + storing) is always a Celery background task — never called synchronously from an API handler
- The RAG fallback phrase ("I don't have that information") is defined in `config.py` as `RAG_FALLBACK_PHRASE` — never hardcoded in the prompt template
- Every retrieval call logs the top-K chunk IDs and similarity scores to the message's `rag_sources` metadata — no silent retrievals

---

## 8. WebSocket Handler Rules

- WebSocket handlers in `ws/chat.py` and `ws/agent.py` do three things only: authenticate the connection, receive messages, and dispatch to service functions
- Handlers never contain business logic — they call `rag/pipeline.py`, `handoff/executor.py`, or `scoring/hook.py` and return the result
- The CalmIQ scoring hook is always fired as a `BackgroundTask` — never awaited in the WebSocket message loop
- Streaming LLM tokens are forwarded to the WebSocket as they arrive — never buffered and sent as one payload
- A connection that fails JWT validation is closed immediately with code 4001 — no message is processed before auth passes

---

## 9. Zustand Rules (Frontend)

- Zustand is the only global state manager across all three frontend packages — no Redux, no Context for shared state
- Context API is permitted only for pure UI configuration: theme colors, font config — never for session or message state
- Every Zustand store has one file. No store spans multiple files.
- Streaming message tokens are appended via a Zustand `appendToken` action — never stored as `useState` in a component that renders the full message list
- Selectors are always memoized — never compute derived values inside a render function that subscribes to a large store slice
- Optimistic UI updates (e.g., agent claims a session) must be paired with a rollback action on server error — never leave the UI in an optimistic state without a confirmed server response

**Re-render check before any component that subscribes to WebSocket data:**
> "Does this component re-render on every token in a streaming response?"
> If yes — it is subscribed to too much state. Use a leaf component with a narrow selector.

---

## 10. Repository Pattern Rules

- Service code never imports SQLAlchemy models or executes queries — it calls repository methods only
- Every repository method has one SQL operation — no method does a query and a mutation in the same call
- The `KnowledgeRepository.search_similar()` method always includes `tenant_id` as a required parameter — no default, no fallback
- Repository implementations live in `repositories/` — abstract interfaces live in `repositories/base.py`
- Swapping the database means writing a new repository implementation file — zero changes to service code

---

## 11. Handoff Rules

These architecture decisions are locked. Do not re-architect these:

- **Trigger detection** happens only in `handoff/triggers.py` — no other file evaluates "should we escalate"
- **Handoff execution** happens only in `handoff/executor.py` — never inline the AI-silencing or queue-push logic in a WebSocket handler
- **Queue depth check** always runs before pushing to the agent queue — never push without checking `AGENT_QUEUE_MAX_DEPTH`
- **AI silencing** sets `ai_silenced: true` in Redis via `session/state.py` — the WebSocket chat handler checks this flag before every LLM call
- **RAG fallback escalation** — if `rag_fallback_count` in session state reaches `RAG_FALLBACK_ESCALATION_THRESHOLD`, `handoff/triggers.py` must treat it as a trigger
- All four trigger sources must produce identical downstream behaviour — the executor does not care which trigger fired

---

## 12. Comments — Small and Purposeful

- **Comment the why, not the what** — the code shows what, the comment explains why
- One short comment per logical block — not per line
- Maximum comment length: one line (under 80 characters)
- Function docstrings: one line only, describing purpose not implementation
- No obvious comments

**Good comment:**
```python
# CalmIQ is optional — skip entirely if webhook URL is not configured
if settings.CALMIQ_WEBHOOK_URL:
    background_tasks.add_task(score_session, session_id, message)
```

**Bad comment:**
```python
# Check if CALMIQ_WEBHOOK_URL is set and add background task if it is
if settings.CALMIQ_WEBHOOK_URL:
    background_tasks.add_task(score_session, session_id, message)
```

---

## 13. Avoid Over-Complexity

- **Simplest working solution first** — optimize only if benchmarks show a problem
- No premature abstraction — don't build a class hierarchy for something a function handles
- No unnecessary design patterns — a simple async function beats a Strategy class in most cases here
- Catch specific exceptions — never use blanket `except Exception` without logging the type and re-raising or handling explicitly
- If a solution feels complex to explain — it is too complex to build. Simplify first.
- Prefer readable over clever — a clear 5-line solution beats a cryptic 1-liner every time

**Complexity check before committing any code:**
> "Can I explain this function in one sentence?"
> If no — it is doing too much. Break it down.

---

## 14. Testing Rules

- Every new function in `rag/`, `handoff/`, `ai/`, and `repositories/` needs a corresponding test
- Tests go in `backend/tests/` matching the module name
- Test with realistic conversational inputs — not just clean synthetic strings
- Test the MockAdapter explicitly — it must return predictable output for every test that touches the AI layer
- Test the RAG fallback path: what happens when no chunk clears the similarity threshold
- Test the handoff trigger for all four sources independently — they must not interfere with each other
- Test tenant isolation: a query for tenant A must never return chunks belonging to tenant B
- Test WebSocket reconnection logic in `useWebSocket.ts` — drop the connection mid-session and verify message continuity
- If a bug is fixed — add a test that would have caught it
- No test should depend on another test's state — each test is fully isolated
- Mock Redis and PostgreSQL in unit tests — never hit live infrastructure in tests
- The MockAdapter must be used in all frontend tests that involve AI responses — no real API calls in CI

---

## 15. Security Rules

These are build-time rules, not review suggestions:

- Never trust `external_id` or any initialisation parameter sent by the widget snippet — always resolve identity server-side from the validated API key
- Never expose internal UUIDs in WebSocket payloads to customer clients — use session tokens only
- Every `KnowledgeRepository` query must include `tenant_id` — enforced at the repository level, not the service level
- JWT verification happens only in `backend/utils/jwt.py` — never inline token decoding in a route or WebSocket handler
- File upload MIME type is validated server-side in the upload handler — never trust the `Content-Type` header sent by the client

---

## 16. When You Are Unsure

If a task requires:
- Creating a file outside the defined structure
- Adding a new public method to the `AIAdapter` interface
- Changing the RAG retrieval formula or similarity threshold defaults
- Changing a locked architecture decision (Redis for session state, pgvector for retrieval, Zustand for frontend state, Celery for background jobs)
- Writing more than 200 lines in a single file
- Adding any real-time audio, voice, or telephony functionality

**Stop and ask the developer before proceeding.**

Do not make assumptions and build anyway. The cost of undoing a structural decision is higher than the cost of asking.

---

## 17. Quick Reference Checklist

Run this before marking any task complete:

- [ ] Did I check if this function already exists in `packages/core` or `backend/utils/`?
- [ ] Is this function under 40 lines?
- [ ] Is this file under 200 lines?
- [ ] Are all constants in `config.py` or `constants.ts`?
- [ ] Is embedding only called through `backend/utils/embedder.py`?
- [ ] Is the WebSocket client only implemented in `packages/core/hooks/useWebSocket.ts`?
- [ ] Is Redis only accessed through `session/state.py`?
- [ ] Is PostgreSQL only accessed through `storage/db.py`?
- [ ] Is the CalmIQ hook fired as a BackgroundTask, not awaited?
- [ ] Is handoff trigger detection only in `handoff/triggers.py`?
- [ ] Is handoff execution only in `handoff/executor.py`?
- [ ] Does every pgvector query include `tenant_id`?
- [ ] Is global frontend state managed only by Zustand (not Context or local useState)?
- [ ] Are streaming tokens appended via a Zustand action, not stored in a rendering component?
- [ ] Did I add a test for new logic?
- [ ] Did I test the MockAdapter / RAG fallback path if I touched AI or RAG code?
- [ ] Are comments explaining why, not what?
- [ ] Can I explain every new function in one sentence?
- [ ] Did I remove all unused imports and dead code?
