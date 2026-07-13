"""
Celery background tasks for the CodePilot AI platform.
"""
import asyncio
from datetime import datetime
from typing import Optional
from app.workers.celery_app import celery_app


def run_async(coro):
    """Run an async coroutine in a sync Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.workers.tasks.analyze_repository",
    max_retries=3,
    default_retry_delay=30,
)
def analyze_repository(
    self,
    repository_id: str,
    github_url: str,
    github_token: Optional[str] = None,
):
    """
    Celery task: analyze a GitHub repository.
    Updates DB with analysis result and triggers embedding generation.
    """
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models import Repository, RepositoryStatus
        from app.services.github_service import GitHubService
        from app.agents.analyzer import run_analyzer_agent
        import re

        # Parse owner/repo from URL
        match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", github_url)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {github_url}")
        owner, repo = match.group(1), match.group(2)

        async with AsyncSessionLocal() as db:
            try:
                # Update status to analyzing
                from sqlalchemy import select
                result = await db.execute(select(Repository).where(Repository.id == repository_id))
                repository = result.scalar_one_or_none()
                if not repository:
                    return {"error": "Repository not found"}

                repository.status = RepositoryStatus.ANALYZING
                await db.commit()

                gh = GitHubService(token=github_token)
                repo_data = await gh.get_repository(owner, repo)
                tree_data = await gh.get_tree(owner, repo)

                readme = ""
                try:
                    readme = await gh.get_file_content(owner, repo, "README.md")
                except Exception:
                    pass

                analysis = await run_analyzer_agent(
                    repo_data=repo_data,
                    tree=tree_data.get("tree", []),
                    readme=readme,
                )

                repository.status = RepositoryStatus.ANALYZED
                repository.analysis_result = analysis
                repository.folder_structure = {"tree": tree_data.get("tree", [])[:100]}
                repository.language = analysis.get("language")
                repository.framework = analysis.get("framework")
                await db.commit()

                return {
                    "status": "completed",
                    "repository_id": repository_id,
                    "analysis": analysis,
                }

            except Exception as e:
                from sqlalchemy import select
                result = await db.execute(select(Repository).where(Repository.id == repository_id))
                repository = result.scalar_one_or_none()
                if repository:
                    repository.status = RepositoryStatus.ERROR
                    await db.commit()
                raise
            finally:
                from app.database import engine
                await engine.dispose()

    return run_async(_run())


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_workflow",
    max_retries=2,
    default_retry_delay=60,
    time_limit=600,  # 10 minutes max
)
def run_workflow(
    self,
    workflow_id: str,
    repository_id: str,
    task_description: str,
    workflow_type: str = "full",
    github_token: Optional[str] = None,
):
    """
    Celery task: run the full multi-agent LangGraph workflow.
    """
    async def _run():
        try:
            from app.database import AsyncSessionLocal
            from app.models import Workflow, WorkflowStatus, AgentRun, AgentType, AgentStatus, Repository
            from app.agents.graph import workflow_graph
            from sqlalchemy import select
            import uuid

            async with AsyncSessionLocal() as db:
                # Get workflow
                wf_result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
                workflow = wf_result.scalar_one_or_none()
                if not workflow:
                    return {"error": "Workflow not found"}

                # Get repo
                repo_result = await db.execute(select(Repository).where(Repository.id == repository_id))
                repository = repo_result.scalar_one_or_none()

                owner, repo_name = "", ""
                if repository and repository.github_url:
                    import re
                    m = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", repository.github_url)
                    if m:
                        owner, repo_name = m.group(1), m.group(2)

                workflow.status = WorkflowStatus.RUNNING
                workflow.started_at = datetime.utcnow()
                await db.commit()

                initial_state = {
                    "workflow_id": workflow_id,
                    "repository_id": repository_id,
                    "task_description": task_description,
                    "workflow_type": workflow_type,
                    "owner": owner,
                    "repo": repo_name,
                    "github_token": github_token,
                    "repo_data": repository.analysis_result or {},
                    "file_tree": (repository.folder_structure or {}).get("tree", []),
                    "readme": "",
                    "analysis_result": repository.analysis_result or {},
                    "knowledge_result": {},
                    "plan": {},
                    "codegen_result": {},
                    "refactor_result": {},
                    "testing_result": {},
                    "review_result": {},
                    "docs_result": {},
                    "github_result": {},
                    "current_agent": "analyzer",
                    "completed_steps": [],
                    "errors": [],
                    "human_approved": False,
                    "status": "running",
                    "logs": [],
                }

                config = {"configurable": {"thread_id": workflow_id}}

                # Run graph until human approval interrupt
                final_state = None
                async for event in workflow_graph.astream(initial_state, config=config):
                    for node_name, node_output in event.items():
                        final_state = node_output

                        # Create agent run record
                        agent_type_map = {
                            "analyzer": AgentType.ANALYZER,
                            "knowledge": AgentType.KNOWLEDGE,
                            "planner": AgentType.PLANNER,
                            "codegen": AgentType.CODEGEN,
                            "refactor": AgentType.REFACTOR,
                            "testing": AgentType.TESTING,
                            "reviewer": AgentType.REVIEWER,
                            "docs": AgentType.DOCS,
                            "github": AgentType.GITHUB,
                        }
                        if node_name in agent_type_map:
                            agent_run = AgentRun(
                                id=uuid.uuid4(),
                                workflow_id=uuid.UUID(workflow_id),
                                agent_type=agent_type_map[node_name],
                                status=AgentStatus.COMPLETED,
                                output_data=node_output,
                                started_at=datetime.utcnow(),
                                completed_at=datetime.utcnow(),
                            )
                            db.add(agent_run)
                            await db.commit()

                # Update workflow status
                current_status = (final_state or {}).get("status", "running")
                if current_status == "awaiting_approval":
                    workflow.status = WorkflowStatus.AWAITING_APPROVAL
                else:
                    workflow.status = WorkflowStatus.COMPLETED if not (final_state or {}).get("errors") else WorkflowStatus.FAILED

                workflow.result = final_state
                workflow.plan = (final_state or {}).get("plan")
                workflow.completed_at = datetime.utcnow()
                await db.commit()

                return {
                    "status": workflow.status.value,
                    "workflow_id": workflow_id,
                    "result": final_state,
                }
        finally:
            from app.database import engine
            await engine.dispose()

    return run_async(_run())


@celery_app.task(
    name="app.workers.tasks.generate_embeddings",
    bind=True,
    max_retries=3,
)
def generate_embeddings(self, repository_id: str, files: list[dict]):
    """Celery task: generate and store code embeddings in Qdrant."""
    async def _run():
        from app.agents.knowledge import run_knowledge_agent
        try:
            result = await run_knowledge_agent(
                repository_id=repository_id,
                files=files,
            )
            return result
        finally:
            from app.database import engine
            await engine.dispose()

    return run_async(_run())
