import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://opendesk_user:opendesk_secure_pass@localhost:5432/opendesk_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_opendesk_core_system_key_12345!")
JWT_ALGORITHM = "HS256"
SESSION_TTL_SECONDS = 86400
