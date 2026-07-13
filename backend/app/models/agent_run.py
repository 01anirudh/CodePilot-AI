import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, Enum as SAEnum, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(str, enum.Enum):
    ANALYZER = "analyzer"
    KNOWLEDGE = "knowledge"
    PLANNER = "planner"
    CODEGEN = "codegen"
    REFACTOR = "refactor"
    TESTING = "testing"
    REVIEWER = "reviewer"
    DOCS = "docs"
    GITHUB = "github"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"))
    agent_type: Mapped[AgentType] = mapped_column(SAEnum(AgentType))
    status: Mapped[AgentStatus] = mapped_column(SAEnum(AgentStatus), default=AgentStatus.PENDING)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    tokens_used: Mapped[int] = mapped_column(default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    log_output: Mapped[str] = mapped_column(Text, nullable=True)
    iteration: Mapped[int] = mapped_column(default=1)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="agent_runs")
