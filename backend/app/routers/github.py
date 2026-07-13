"""
GitHub router — webhook receiver and PR management.
"""
import hashlib
import hmac
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import PullRequest, PRStatus
from app.schemas.auth import PullRequestResponse, PRApproval
from app.routers.auth import get_current_user
from app.models import User
from app.config import settings
from app.core.audit import log_action

router = APIRouter(prefix="/github", tags=["GitHub"])


@router.get("/pull-requests", response_model=list[PullRequestResponse])
async def list_pull_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    result = await db.execute(
        select(PullRequest)
        .offset(skip)
        .limit(limit)
        .order_by(PullRequest.created_at.desc())
    )
    return result.scalars().all()


@router.get("/pull-requests/{pr_id}", response_model=PullRequestResponse)
async def get_pull_request(
    pr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(PullRequest).where(PullRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
    return pr


@router.post("/pull-requests/{pr_id}/approve", response_model=PullRequestResponse)
async def approve_pull_request(
    pr_id: uuid.UUID,
    approval: PRApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(PullRequest).where(PullRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    if approval.approved:
        pr.status = PRStatus.APPROVED
        pr.approved_by_id = current_user.id
        await log_action(db, "pr.approved", str(current_user.id), "pull_request", str(pr_id),
                         {"comment": approval.comment})
    else:
        pr.status = PRStatus.REJECTED
        await log_action(db, "pr.rejected", str(current_user.id), "pull_request", str(pr_id),
                         {"comment": approval.comment})

    return pr


@router.post("/webhook")
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str = Header(None),
):
    """Receive GitHub webhook events."""
    body = await request.body()

    # Verify signature
    if settings.GITHUB_WEBHOOK_SECRET and x_hub_signature_256:
        expected = "sha256=" + hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = json.loads(body)
    event_type = request.headers.get("X-GitHub-Event", "unknown")

    await log_action(db, f"github.webhook.{event_type}", None, "github", None,
                     {"action": payload.get("action"), "repo": payload.get("repository", {}).get("full_name")})

    return {"received": True, "event": event_type}
