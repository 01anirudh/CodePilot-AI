"""
Repositories router — CRUD and analysis trigger.
"""
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Repository, RepositoryStatus
from app.schemas.auth import RepositoryCreate, RepositoryResponse
from app.routers.auth import get_current_user
from app.models import User
from app.core.audit import log_action

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("/", response_model=list[RepositoryResponse])
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    result = await db.execute(
        select(Repository)
        .where(Repository.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Repository.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=RepositoryResponse, status_code=201)
async def create_repository(
    data: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Parse name from URL if not provided
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
        owner_id=current_user.id,
        name=name or "unnamed",
        full_name=full_name,
        github_url=data.github_url,
        description=data.description,
        status=RepositoryStatus.PENDING,
    )
    db.add(repo)
    await db.flush()
    await log_action(db, "repository.created", str(current_user.id), "repository", str(repo.id))

    # Trigger async analysis
    background_tasks.add_task(
        _trigger_analysis,
        str(repo.id),
        data.github_url,
        current_user.github_token,
    )

    return repo


async def _trigger_analysis(repo_id: str, github_url: str, github_token: str):
    from app.workers.tasks import analyze_repository
    task = analyze_repository.delay(repo_id, github_url, github_token)
    # Update celery task ID
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        from sqlalchemy import update
        await db.execute(
            update(Repository)
            .where(Repository.id == repo_id)
            .values(status=RepositoryStatus.ANALYZING)
        )
        await db.commit()


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repository_id}", status_code=204)
async def delete_repository(
    repository_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Repository).where(
            Repository.id == repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    await db.delete(repo)
    await log_action(db, "repository.deleted", str(current_user.id), "repository", str(repository_id))
