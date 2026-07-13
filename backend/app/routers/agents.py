"""
Agents router — agent status, capabilities, and semantic search.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import AgentRun, AgentType
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/agents", tags=["Agents"])

AGENT_METADATA = {
    "analyzer": {
        "name": "Repository Analyzer",
        "description": "Reads repository structure, detects frameworks, identifies dependencies, and builds an architecture map.",
        "capabilities": ["Architecture analysis", "Dependency detection", "Framework identification", "Code complexity scoring"],
        "icon": "🔍",
        "color": "#6366f1",
    },
    "knowledge": {
        "name": "Knowledge Agent",
        "description": "Generates embeddings for code, comments, docs, and commits. Stores them in Qdrant for semantic search.",
        "capabilities": ["Code chunking", "Semantic embeddings", "Vector storage", "Codebase search"],
        "icon": "🧠",
        "color": "#8b5cf6",
    },
    "planner": {
        "name": "Planner Agent",
        "description": "Receives a task, breaks it into sub-tasks, and assigns them to specific agents in an optimal order.",
        "capabilities": ["Task decomposition", "Agent orchestration", "Dependency mapping", "Complexity estimation"],
        "icon": "📋",
        "color": "#06b6d4",
    },
    "codegen": {
        "name": "Code Generation Agent",
        "description": "Generates production-quality code: classes, methods, APIs, SQL queries, and components.",
        "capabilities": ["Function generation", "API endpoints", "SQL queries", "Component scaffolding"],
        "icon": "⚡",
        "color": "#f59e0b",
    },
    "refactor": {
        "name": "Refactoring Agent",
        "description": "Detects duplicated code, long methods, dead code, and SOLID violations. Suggests and applies improvements.",
        "capabilities": ["Code smell detection", "SOLID violation checks", "Dead code removal", "Complexity reduction"],
        "icon": "🔧",
        "color": "#10b981",
    },
    "testing": {
        "name": "Testing Agent",
        "description": "Automatically creates unit tests, integration tests, mock objects, and edge case coverage.",
        "capabilities": ["Unit tests", "Integration tests", "Mock generation", "Edge case coverage"],
        "icon": "🧪",
        "color": "#3b82f6",
    },
    "reviewer": {
        "name": "Code Review Agent",
        "description": "Reviews complexity, security vulnerabilities, performance bottlenecks, and maintainability.",
        "capabilities": ["Security scanning", "Performance review", "Complexity analysis", "Maintainability scoring"],
        "icon": "👁️",
        "color": "#ef4444",
    },
    "docs": {
        "name": "Documentation Agent",
        "description": "Creates README, API docs, UML class diagrams, and sequence diagrams automatically.",
        "capabilities": ["README generation", "API documentation", "UML diagrams", "Sequence diagrams"],
        "icon": "📚",
        "color": "#84cc16",
    },
    "github": {
        "name": "GitHub Agent",
        "description": "Creates branches, commits code, and opens pull requests with rich descriptions.",
        "capabilities": ["Branch creation", "Code commits", "PR generation", "CI/CD triggering"],
        "icon": "🐙",
        "color": "#f97316",
    },
}


@router.get("/")
async def list_agents():
    """List all available agents with metadata."""
    return [{"id": k, **v} for k, v in AGENT_METADATA.items()]


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get metadata for a specific agent."""
    if agent_id not in AGENT_METADATA:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"id": agent_id, **AGENT_METADATA[agent_id]}


@router.get("/{agent_id}/runs")
async def get_agent_runs(
    agent_id: str,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent runs for a specific agent."""
    try:
        agent_type = AgentType(agent_id)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Invalid agent type")

    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.agent_type == agent_type)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()
    return runs


@router.post("/search")
async def semantic_search(
    query: str,
    repository_id: str,
    limit: int = Query(5, le=20),
    current_user: User = Depends(get_current_user),
):
    """Semantic search over the codebase knowledge base."""
    from app.agents.knowledge import semantic_search as _search
    results = await _search(query, repository_id, limit)
    return {"query": query, "results": results}
