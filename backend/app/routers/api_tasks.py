"""
Production API endpoints for CodePilot AI:
- POST /api/projects
- GET  /api/projects
- POST /api/agents/run
- GET  /api/tasks/{task_id}
- GET  /api/tasks/{task_id}/status
- POST /api/tasks/{task_id}/approve
- GET  /api/health
"""
import uuid
import re
import logging
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.database import get_db, AsyncSessionLocal
from app.models import Workflow, WorkflowStatus, WorkflowType, Repository, RepositoryStatus, User, UserRole
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Production Tasks & Projects API"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ProjectCreateRequest(BaseModel):
    name: Optional[str] = None
    github_url: str = Field(..., description="GitHub repository URL")
    description: Optional[str] = None
    default_branch: Optional[str] = "main"


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    full_name: Optional[str]
    github_url: Optional[str]
    description: Optional[str]
    status: str
    default_branch: str
    created_at: datetime


class AgentRunRequest(BaseModel):
    project_id: Optional[uuid.UUID] = None
    repository_id: Optional[uuid.UUID] = None
    task: Optional[str] = None
    task_description: Optional[str] = None
    workflow_type: Optional[str] = "full"
    github_token: Optional[str] = None


class AgentRunResponse(BaseModel):
    task_id: str
    repository: str
    status: str
    current_agent: str
    iteration: int
    created_at: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    current_agent: str
    iteration: int
    completed: bool


class TaskApprovalRequest(BaseModel):
    approved: bool = True
    comment: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    database: str
    redis: str
    qdrant: str


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def get_or_create_default_user(db: AsyncSession) -> User:
    """Ensure a default user exists for unauthenticated API requests."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email="system@codepilot.ai",
            username="codepilot_user",
            full_name="CodePilot User",
            hashed_password="system-managed-user-nopass",
            role=UserRole.DEVELOPER,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def _dispatch_workflow_async(workflow_id: str, repository_id: str, task_desc: str, wf_type: str, gh_token: Optional[str]):
    """Safely trigger Celery workflow in background without blocking web request."""
    try:
        from app.workers.tasks import run_workflow
        task = run_workflow.delay(workflow_id, repository_id, task_desc, wf_type, gh_token)
        async with AsyncSessionLocal() as db:
            from sqlalchemy import update
            await db.execute(
                update(Workflow)
                .where(Workflow.id == uuid.UUID(workflow_id))
                .values(celery_task_id=task.id)
            )
            await db.commit()
    except Exception as e:
        logger.warning(f"Celery dispatch failed or broker offline: {e}")



# ─── Projects Endpoints ───────────────────────────────────────────────────────

@router.post("/api/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/projects
    Register a new project / GitHub repository.
    """
    user = await get_or_create_default_user(db)

    name = data.name
    full_name = None
    if data.github_url:
        m = re.search(r"github\.com/([^/]+/[^/]+?)(?:\.git)?$", data.github_url)
        if m:
            full_name = m.group(1)
            if not name:
                name = full_name.split("/")[-1]

    repo = Repository(
        id=uuid.uuid4(),
        owner_id=user.id,
        name=name or "unnamed-project",
        full_name=full_name,
        github_url=data.github_url,
        description=data.description,
        default_branch=data.default_branch or "main",
        status=RepositoryStatus.PENDING,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    # Trigger background analysis
    try:
        from app.workers.tasks import analyze_repository
        analyze_repository.delay(str(repo.id), data.github_url, user.github_token)
    except Exception as e:
        logger.warning(f"Could not queue repo analysis task: {e}")

    return ProjectResponse(
        id=repo.id,
        name=repo.name,
        full_name=repo.full_name,
        github_url=repo.github_url,
        description=repo.description,
        status=repo.status.value if hasattr(repo.status, "value") else str(repo.status),
        default_branch=repo.default_branch,
        created_at=repo.created_at,
    )


@router.get("/api/projects", response_model=list[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """GET /api/projects — List all projects."""
    result = await db.execute(
        select(Repository).offset(skip).limit(limit).order_by(Repository.created_at.desc())
    )
    repos = result.scalars().all()
    return [
        ProjectResponse(
            id=r.id,
            name=r.name,
            full_name=r.full_name,
            github_url=r.github_url,
            description=r.description,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            default_branch=r.default_branch,
            created_at=r.created_at,
        )
        for r in repos
    ]


# ─── Agents Run Endpoint ──────────────────────────────────────────────────────

@router.post("/api/agents/run", response_model=AgentRunResponse, status_code=202)
async def run_agent_workflow(
    data: AgentRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/agents/run
    Trigger asynchronous multi-agent workflow execution.
    Immediately returns a task_id without blocking.
    """
    repo_id = data.project_id or data.repository_id
    task_desc = data.task or data.task_description

    if not task_desc:
        raise HTTPException(status_code=400, detail="Missing task description ('task' or 'task_description')")

    repo = None
    if repo_id:
        result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()

    if not repo:
        # Fall back to first available repository or create default
        result = await db.execute(select(Repository).limit(1))
        repo = result.scalar_one_or_none()
        if not repo:
            user = await get_or_create_default_user(db)
            repo = Repository(
                id=uuid.uuid4(),
                owner_id=user.id,
                name="codepilot-workspace",
                full_name="local/codepilot-workspace",
                github_url="https://github.com/local/codepilot-workspace",
                description="Default workspace repository",
                status=RepositoryStatus.ANALYZED,
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)

    user = await get_or_create_default_user(db)

    try:
        wf_type = WorkflowType(data.workflow_type)
    except ValueError:
        wf_type = WorkflowType.FULL

    workflow = Workflow(
        id=uuid.uuid4(),
        repository_id=repo.id,
        created_by=user.id,
        type=wf_type,
        status=WorkflowStatus.QUEUED,
        current_agent="supervisor",
        iteration=0,
        task_description=task_desc,
        started_at=datetime.utcnow(),
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    # Asynchronously dispatch to Celery / worker
    background_tasks.add_task(
        _dispatch_workflow_async,
        str(workflow.id),
        str(repo.id),
        task_desc,
        data.workflow_type or "full",
        data.github_token or user.github_token,
    )

    return AgentRunResponse(
        task_id=str(workflow.id),
        repository=repo.full_name or repo.name,
        status=workflow.status.value if hasattr(workflow.status, "value") else str(workflow.status),
        current_agent="supervisor",
        iteration=0,
        created_at=workflow.created_at.isoformat(),
    )


# ─── Tasks Query & Status Endpoints ───────────────────────────────────────────

@router.get("/api/tasks/{task_id}")
async def get_task_details(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/tasks/{task_id}
    Returns structured persistent state:
    {
      "task_id": "...",
      "repository": "...",
      "status": "...",
      "current_agent": "...",
      "iteration": 0,
      "plan": [],
      "tool_results": [],
      "errors": [],
      "files_changed": [],
      "messages": []
    }
    """
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.repository), selectinload(Workflow.agent_runs))
        .where(Workflow.id == task_id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Task not found")

    return workflow.to_structured_state()


@router.get("/api/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/tasks/{task_id}/status
    Lightweight status check for polling agents.
    """
    result = await db.execute(select(Workflow).where(Workflow.id == task_id))
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Task not found")

    status_str = workflow.status.value if hasattr(workflow.status, "value") else str(workflow.status)
    is_completed = status_str in ["COMPLETED", "FAILED", "completed", "failed"]

    return TaskStatusResponse(
        task_id=str(workflow.id),
        status=status_str,
        current_agent=workflow.current_agent or "",
        iteration=workflow.iteration or 0,
        completed=is_completed,
    )


@router.post("/api/tasks/{task_id}/approve")
async def approve_task(
    task_id: uuid.UUID,
    approval: TaskApprovalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/tasks/{task_id}/approve
    Approve or reject a workflow paused at WAITING_FOR_APPROVAL.
    Resumes execution asynchronously.
    """
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.repository))
        .where(Workflow.id == task_id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Task not found")

    if approval.approved:
        workflow.status = WorkflowStatus.CODING
        workflow.current_agent = "github"
        if isinstance(workflow.result, dict):
            workflow.result["human_approved"] = True
        await db.commit()

        # Trigger worker resume
        try:
            from app.workers.tasks import resume_workflow
            resume_workflow.delay(str(workflow.id))
        except Exception as e:
            logger.warning(f"Could not dispatch resume_workflow to Celery: {e}")
    else:

        workflow.status = WorkflowStatus.FAILED
        workflow.error_message = f"Rejected by user: {approval.comment or 'No comment provided'}"
        workflow.completed_at = datetime.utcnow()
        await db.commit()

    return workflow.to_structured_state()


# ─── Health Endpoint ──────────────────────────────────────────────────────────

@router.get("/api/health", response_model=HealthResponse)
async def api_health_check(db: AsyncSession = Depends(get_db)):
    """GET /api/health — System health check verifying DB, Redis, and Qdrant."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected: {e}"

    redis_status = "not_configured"
    if settings.REDIS_URL:
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.0)
            await r.ping()
            await r.aclose()
            redis_status = "connected"
        except Exception as e:
            redis_status = f"unreachable: {e}"

    qdrant_status = "not_configured"
    if settings.QDRANT_URL:
        try:
            from app.services.qdrant_service import get_qdrant_client
            client = get_qdrant_client()
            await client.get_collections()
            qdrant_status = "connected"
        except Exception as e:
            qdrant_status = f"unreachable: {e}"

    overall_status = "healthy" if ("disconnected" not in db_status) else "degraded"

    return HealthResponse(
        status=overall_status,
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database=db_status,
        redis=redis_status,
        qdrant=qdrant_status,
    )
