import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class WorkflowStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowType(str, enum.Enum):
    FULL = "full"
    BUG_FIX = "bug_fix"
    CODE_REVIEW = "code_review"
    GENERATE_TESTS = "generate_tests"
    GENERATE_DOCS = "generate_docs"
    REFACTOR = "refactor"
    ANALYZE = "analyze"


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[WorkflowType] = mapped_column(SAEnum(WorkflowType), default=WorkflowType.FULL)
    status: Mapped[WorkflowStatus] = mapped_column(SAEnum(WorkflowStatus), default=WorkflowStatus.QUEUED)
    task_description: Mapped[str] = mapped_column(Text, nullable=True)  # e.g. "Fix the login bug"
    plan: Mapped[dict] = mapped_column(JSON, nullable=True)  # Planner agent output
    result: Mapped[dict] = mapped_column(JSON, nullable=True)  # Final aggregated output
    celery_task_id: Mapped[str] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    repository: Mapped["Repository"] = relationship("Repository", back_populates="workflows")
    created_by_user: Mapped["User"] = relationship("User", back_populates="workflows")
    agent_runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="workflow")
    pull_requests: Mapped[list["PullRequest"]] = relationship("PullRequest", back_populates="workflow")
