"""
Pydantic schemas for request/response models.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
import uuid


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    avatar_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ─── Repository ───────────────────────────────────────────────────────────────

class RepositoryCreate(BaseModel):
    github_url: str
    name: Optional[str] = None
    description: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    full_name: Optional[str]
    github_url: Optional[str]
    description: Optional[str]
    language: Optional[str]
    framework: Optional[str]
    stars: int
    status: str
    analysis_result: Optional[dict]
    embedding_count: int
    default_branch: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Workflow ─────────────────────────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    repository_id: uuid.UUID
    task_description: str
    workflow_type: str = "full"


class WorkflowResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    type: str
    status: str
    task_description: Optional[str]
    plan: Optional[dict]
    result: Optional[dict]
    celery_task_id: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── AgentRun ─────────────────────────────────────────────────────────────────

class AgentRunResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    agent_type: str
    status: str
    input_data: Optional[dict]
    output_data: Optional[dict]
    tokens_used: int
    duration_seconds: Optional[float]
    error_message: Optional[str]
    log_output: Optional[str]
    iteration: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── AuditLog ─────────────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── PullRequest ──────────────────────────────────────────────────────────────

class PRApproval(BaseModel):
    approved: bool
    comment: Optional[str] = None


class PullRequestResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    repository_id: uuid.UUID
    title: str
    description: Optional[str]
    branch_name: Optional[str]
    base_branch: str
    status: str
    github_pr_number: Optional[int]
    github_pr_url: Optional[str]
    files_changed: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}
