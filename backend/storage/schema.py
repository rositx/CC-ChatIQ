import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Integer, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector
from backend.config import EMBEDDING_DIMENSIONS

Base = declarative_base()

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    agent_id = Column(UUID(as_uuid=True), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String, default="active")  # active | escalated | resolved | abandoned
    escalation_trigger = Column(String, nullable=True)
    peak_score = Column(Float, nullable=True)
    resolution_type = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "active")
        super().__init__(**kwargs)

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    rag_sources = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)

class KnowledgeChunkModel(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    document_title = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# HNSW index for sub-50ms cosine distance searches
Index(
    "idx_knowledge_chunks_embedding",
    KnowledgeChunkModel.embedding,
    postgresql_using="hnsw",
    postgresql_ops={"embedding": "vector_cosine_ops"}
)
