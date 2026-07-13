import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, Enum as SAEnum, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class PRStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"
    CLOSED = "closed"


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"))
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=True)
    base_branch: Mapped[str] = mapped_column(String(255), default="main")
    status: Mapped[PRStatus] = mapped_column(SAEnum(PRStatus), default=PRStatus.DRAFT)
    github_pr_number: Mapped[int] = mapped_column(Integer, nullable=True)
    github_pr_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    diff: Mapped[str] = mapped_column(Text, nullable=True)
    files_changed: Mapped[dict] = mapped_column(JSON, nullable=True)
    review_comments: Mapped[str] = mapped_column(Text, nullable=True)
    approved_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="pull_requests")
    repository: Mapped["Repository"] = relationship("Repository", back_populates="pull_requests")
