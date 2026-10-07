import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, DateTime, Enum as SAEnum, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database import Base


class WorkflowStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    ANALYZING = "ANALYZING"
    PLANNING = "PLANNING"
    CODING = "CODING"
    TESTING = "TESTING"
    REVIEWING = "REVIEWING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    # Legacy/compatibility aliases
    queued = "QUEUED"
    running = "RUNNING"
    RUNNING = "RUNNING"
    awaiting_approval = "WAITING_FOR_APPROVAL"
    approved = "APPROVED"
    rejected = "REJECTED"
    completed = "COMPLETED"
    failed = "FAILED"


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
    type: Mapped[WorkflowType] = mapped_column(SAEnum(WorkflowType, native_enum=False), default=WorkflowType.FULL)
    status: Mapped[WorkflowStatus] = mapped_column(SAEnum(WorkflowStatus, native_enum=False), default=WorkflowStatus.QUEUED)
    task_description: Mapped[str] = mapped_column(Text, nullable=True)  # e.g. "Fix the login bug"
    current_agent: Mapped[str] = mapped_column(String(50), nullable=True, default="supervisor")
    iteration: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    plan: Mapped[dict] = mapped_column(JSON, nullable=True)  # Planner agent output
    tool_results: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    errors: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    files_changed: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    messages: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
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

    def to_structured_state(self) -> dict:
        repo_name = ""
        try:
            if "repository" in self.__dict__ and self.repository:
                repo_name = getattr(self.repository, "full_name", None) or getattr(self.repository, "name", "")
        except Exception:
            pass

        plan_list = []
        if isinstance(self.plan, list):
            plan_list = self.plan
        elif isinstance(self.plan, dict):
            plan_list = self.plan.get("steps", [])

        files = self.files_changed or []
        if not files and isinstance(self.result, dict):
            codegen_res = self.result.get("codegen_result", {})
            if isinstance(codegen_res, dict) and "files" in codegen_res:
                files = codegen_res.get("files", [])

        tools = self.tool_results or []
        if not tools and "agent_runs" in self.__dict__ and self.agent_runs:
            try:
                tools = [
                    {
                        "agent": ar.agent_type.value if hasattr(ar.agent_type, "value") else str(ar.agent_type),
                        "status": ar.status.value if hasattr(ar.status, "value") else str(ar.status),
                        "duration_seconds": ar.duration_seconds,
                    }
                    for ar in self.agent_runs
                ]
            except Exception:
                pass


        msgs = self.messages or []
        if not msgs and isinstance(self.result, dict):
            msgs = self.result.get("logs", [])

        errs = self.errors or []
        if not errs and isinstance(self.result, dict):
            errs = self.result.get("errors", [])
        if self.error_message and not errs:
            errs = [{"error": self.error_message}]

        status_val = self.status.value if hasattr(self.status, "value") else str(self.status)

        return {
            "task_id": str(self.id),
            "repository": repo_name,
            "status": status_val,
            "current_agent": self.current_agent or "",
            "iteration": self.iteration or 0,
            "plan": plan_list,
            "tool_results": tools,
            "errors": errs,
            "files_changed": files,
            "messages": msgs,
        }

