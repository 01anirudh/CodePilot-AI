"""
Workflows router — create, monitor, approve, and stream workflow executions.
"""
import uuid
import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Workflow, WorkflowStatus, WorkflowType, AgentRun, PullRequest, PRStatus, Repository
from app.schemas.auth import WorkflowCreate, WorkflowResponse, AgentRunResponse, PRApproval, PullRequestResponse
from app.routers.auth import get_current_user
from app.models import User
from app.core.audit import log_action

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.get("/", response_model=list[WorkflowResponse])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
):
    result = await db.execute(
        select(Workflow)
        .where(Workflow.created_by == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Workflow.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate repository access
    repo_result = await db.execute(
        select(Repository).where(
            Repository.id == data.repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        wf_type = WorkflowType(data.workflow_type)
    except ValueError:
        wf_type = WorkflowType.FULL

    workflow = Workflow(
        id=uuid.uuid4(),
        repository_id=data.repository_id,
        created_by=current_user.id,
        type=wf_type,
        status=WorkflowStatus.QUEUED,
        task_description=data.task_description,
    )
    db.add(workflow)
    await db.flush()
    await log_action(db, "workflow.created", str(current_user.id), "workflow", str(workflow.id),
                     {"task": data.task_description, "type": data.workflow_type})

    # Trigger Celery workflow
    background_tasks.add_task(
        _trigger_workflow,
        str(workflow.id),
        str(data.repository_id),
        data.task_description,
        data.workflow_type,
        current_user.github_token,
    )

    return workflow


async def _trigger_workflow(workflow_id, repository_id, task_description, workflow_type, github_token):
    from app.workers.tasks import run_workflow
    task = run_workflow.delay(workflow_id, repository_id, task_description, workflow_type, github_token)
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        from sqlalchemy import update
        await db.execute(
            update(Workflow)
            .where(Workflow.id == workflow_id)
            .values(celery_task_id=task.id)
        )
        await db.commit()


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.created_by == current_user.id,
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.get("/{workflow_id}/agent-runs", response_model=list[AgentRunResponse])
async def get_agent_runs(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.workflow_id == workflow_id)
        .order_by(AgentRun.created_at.asc())
    )
    return result.scalars().all()


@router.get("/{workflow_id}/stream")
async def stream_workflow_logs(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Server-Sent Events endpoint for real-time workflow log streaming."""

    async def event_generator() -> AsyncGenerator[str, None]:
        prev_count = 0
        max_polls = 120  # 2 minutes max streaming

        for _ in range(max_polls):
            result = await db.execute(
                select(Workflow).where(Workflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()
            if not workflow:
                yield f"data: {json.dumps({'error': 'Workflow not found'})}\n\n"
                break

            # Send workflow status
            logs = (workflow.result or {}).get("logs", [])
            if len(logs) > prev_count:
                for log_entry in logs[prev_count:]:
                    yield f"data: {json.dumps(log_entry)}\n\n"
                prev_count = len(logs)

            # Check terminal states
            if workflow.status in (
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
                WorkflowStatus.AWAITING_APPROVAL,
                WorkflowStatus.REJECTED,
            ):
                yield f"data: {json.dumps({'status': workflow.status.value, 'done': True})}\n\n"
                break

            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{workflow_id}/approve", response_model=WorkflowResponse)
async def approve_workflow(
    workflow_id: uuid.UUID,
    approval: PRApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Human-in-the-loop approval for pending workflows."""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.created_by == current_user.id,
        )
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status != WorkflowStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"Workflow is not awaiting approval (status: {workflow.status})")

    if approval.approved:
        workflow.status = WorkflowStatus.APPROVED
        await log_action(db, "workflow.approved", str(current_user.id), "workflow", str(workflow_id),
                         {"comment": approval.comment})
        # Resume the LangGraph workflow with approval
        from app.agents.graph import workflow_graph
        config = {"configurable": {"thread_id": str(workflow_id)}}
        # Update state with human approval
        await workflow_graph.aupdate_state(
            config,
            {"human_approved": True},
            as_node="human_approval",
        )
    else:
        workflow.status = WorkflowStatus.REJECTED
        await log_action(db, "workflow.rejected", str(current_user.id), "workflow", str(workflow_id),
                         {"comment": approval.comment})

    return workflow
