import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://cc_chatiq_user:cc_chatiq_secure_pass@localhost:5432/cc_chatiq_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_cc_chatiq_core_system_key_12345!")
JWT_ALGORITHM = "HS256"
SESSION_TTL_SECONDS = 86400

# RAG & AI Configs
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")
AI_MODEL_OPENAI = os.getenv("AI_MODEL_OPENAI", "gpt-4o")
AI_MODEL_ANTHROPIC = os.getenv("AI_MODEL_ANTHROPIC", "claude-sonnet-4-20250514")
AI_MODEL_GROQ = os.getenv("AI_MODEL_GROQ", "llama-3.1-8b-instant")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.3"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "1024"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))

RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.72"))
RAG_MAX_CONTEXT_TOKENS = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "2000"))
RAG_FALLBACK_ESCALATION_THRESHOLD = int(os.getenv("RAG_FALLBACK_ESCALATION_THRESHOLD", "3"))
RAG_FALLBACK_PHRASE = "I don't have that information — let me connect you with a team member."

KEYWORD_TRIGGER_LIST = ["cancel", "refund", "manager", "human", "representative", "useless", "broken"]
