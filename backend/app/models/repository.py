import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, Enum as SAEnum, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class RepositoryStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ERROR = "error"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), nullable=True)  # e.g. "owner/repo"
    github_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(100), nullable=True)
    framework: Mapped[str] = mapped_column(String(100), nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[RepositoryStatus] = mapped_column(SAEnum(RepositoryStatus), default=RepositoryStatus.PENDING)
    analysis_result: Mapped[dict] = mapped_column(JSON, nullable=True)  # Architecture, deps, etc.
    folder_structure: Mapped[dict] = mapped_column(JSON, nullable=True)
    dependencies: Mapped[dict] = mapped_column(JSON, nullable=True)
    embedding_count: Mapped[int] = mapped_column(Integer, default=0)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["User"] = relationship("User", back_populates="repositories")
    workflows: Mapped[list["Workflow"]] = relationship("Workflow", back_populates="repository")
    pull_requests: Mapped[list["PullRequest"]] = relationship("PullRequest", back_populates="repository")
