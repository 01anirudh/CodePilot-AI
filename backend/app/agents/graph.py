"""
LangGraph Workflow Orchestration — wires all 9 agents into a StateGraph
with human-in-the-loop checkpoint and streaming support.
"""
from typing import TypedDict, Any, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator


class WorkflowState(TypedDict):
    """Shared state flowing through the agent pipeline."""
    # Input
    workflow_id: str
    repository_id: str
    task_description: str
    workflow_type: str
    owner: str
    repo: str
    github_token: Optional[str]

    # Repository data
    repo_data: dict
    file_tree: list
    readme: str

    # Agent outputs
    analysis_result: dict
    knowledge_result: dict
    plan: dict
    codegen_result: dict
    refactor_result: dict
    testing_result: dict
    review_result: dict
    docs_result: dict
    github_result: dict

    # Control flow
    current_agent: str
    completed_steps: Annotated[list, operator.add]
    errors: Annotated[list, operator.add]
    human_approved: bool
    status: str
    logs: Annotated[list, operator.add]


# ─── Node Functions ──────────────────────────────────────────────────────────

async def analyzer_node(state: WorkflowState) -> dict:
    from app.agents.analyzer import run_analyzer_agent
    try:
        result = await run_analyzer_agent(
            repo_data=state.get("repo_data", {}),
            tree=state.get("file_tree", []),
            readme=state.get("readme", ""),
        )
        return {
            "analysis_result": result,
            "current_agent": "knowledge",
            "completed_steps": ["analyzer"],
            "logs": [{"agent": "analyzer", "status": "completed", "message": f"Analyzed repo: {result.get('language', '?')} / {result.get('framework', '?')}"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "analyzer", "error": str(e)}],
            "logs": [{"agent": "analyzer", "status": "error", "message": str(e)}],
            "current_agent": "planner",  # Continue with defaults
            "completed_steps": ["analyzer"],
            "analysis_result": {},
        }


async def knowledge_node(state: WorkflowState) -> dict:
    from app.agents.knowledge import run_knowledge_agent
    try:
        # Build files list from tree (simplified — in production fetch content)
        files = [
            {"path": item["path"], "content": f"# {item['path']}\n# File content"}
            for item in state.get("file_tree", [])
            if item.get("type") == "blob"
        ][:50]

        result = await run_knowledge_agent(
            repository_id=state["repository_id"],
            files=files,
        )
        return {
            "knowledge_result": result,
            "current_agent": "planner",
            "completed_steps": ["knowledge"],
            "logs": [{"agent": "knowledge", "status": "completed", "message": f"Embedded {result.get('chunks_embedded', 0)} chunks"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "knowledge", "error": str(e)}],
            "logs": [{"agent": "knowledge", "status": "error", "message": str(e)}],
            "current_agent": "planner",
            "completed_steps": ["knowledge"],
            "knowledge_result": {},
        }


async def planner_node(state: WorkflowState) -> dict:
    from app.agents.planner import run_planner_agent
    try:
        plan = await run_planner_agent(
            task_description=state["task_description"],
            repo_analysis=state.get("analysis_result", {}),
            workflow_type=state.get("workflow_type", "full"),
        )
        return {
            "plan": plan,
            "current_agent": "codegen",
            "completed_steps": ["planner"],
            "logs": [{"agent": "planner", "status": "completed", "message": f"Plan created: {len(plan.get('steps', []))} steps"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "planner", "error": str(e)}],
            "logs": [{"agent": "planner", "status": "error", "message": str(e)}],
            "current_agent": "codegen",
            "completed_steps": ["planner"],
            "plan": {},
        }


async def codegen_node(state: WorkflowState) -> dict:
    from app.agents.codegen import run_codegen_agent
    from app.agents.knowledge import semantic_search
    try:
        # Get relevant code snippets
        relevant_code = []
        try:
            relevant_code = await semantic_search(
                state["task_description"],
                state["repository_id"],
                limit=5,
            )
        except Exception:
            pass

        plan_steps = state.get("plan", {}).get("steps", [])
        codegen_step = next((s for s in plan_steps if s.get("agent") == "codegen"), {"action": "Generate code", "output": "code_files"})

        result = await run_codegen_agent(
            task_description=state["task_description"],
            plan_step=codegen_step,
            repo_analysis=state.get("analysis_result", {}),
            relevant_code=relevant_code,
        )
        return {
            "codegen_result": result,
            "current_agent": "testing",
            "completed_steps": ["codegen"],
            "logs": [{"agent": "codegen", "status": "completed", "message": f"Generated {len(result.get('files', []))} files"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "codegen", "error": str(e)}],
            "logs": [{"agent": "codegen", "status": "error", "message": str(e)}],
            "current_agent": "testing",
            "completed_steps": ["codegen"],
            "codegen_result": {"files": []},
        }


async def testing_node(state: WorkflowState) -> dict:
    from app.agents.testing import run_testing_agent
    try:
        result = await run_testing_agent(
            generated_code=state.get("codegen_result", {}),
            repo_analysis=state.get("analysis_result", {}),
            task_description=state["task_description"],
        )
        return {
            "testing_result": result,
            "current_agent": "reviewer",
            "completed_steps": ["testing"],
            "logs": [{"agent": "testing", "status": "completed", "message": f"Generated {result.get('total_test_count', 0)} tests ({result.get('coverage_estimate', '?')} coverage)"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "testing", "error": str(e)}],
            "logs": [{"agent": "testing", "status": "error", "message": str(e)}],
            "current_agent": "reviewer",
            "completed_steps": ["testing"],
            "testing_result": {},
        }


async def refactor_node(state: WorkflowState) -> dict:
    from app.agents.refactor import run_refactor_agent
    try:
        files = state.get("codegen_result", {}).get("files", [])
        result = await run_refactor_agent(
            files=files,
            repo_analysis=state.get("analysis_result", {}),
        )
        return {
            "refactor_result": result,
            "completed_steps": ["refactor"],
            "logs": [{"agent": "refactor", "status": "completed", "message": f"Found {len(result.get('issues', []))} issues, quality improved {result.get('quality_score_before', 0)} → {result.get('quality_score_after', 0)}"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "refactor", "error": str(e)}],
            "logs": [{"agent": "refactor", "status": "error", "message": str(e)}],
            "completed_steps": ["refactor"],
            "refactor_result": {},
        }


async def reviewer_node(state: WorkflowState) -> dict:
    from app.agents.reviewer import run_reviewer_agent
    try:
        result = await run_reviewer_agent(
            generated_code=state.get("codegen_result", {}),
            test_results=state.get("testing_result", {}),
            repo_analysis=state.get("analysis_result", {}),
        )
        return {
            "review_result": result,
            "current_agent": "docs",
            "completed_steps": ["reviewer"],
            "logs": [{"agent": "reviewer", "status": "completed", "message": f"Review: {result.get('verdict', 'approve')} (score: {result.get('overall_score', 0)}/100)"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "reviewer", "error": str(e)}],
            "logs": [{"agent": "reviewer", "status": "error", "message": str(e)}],
            "current_agent": "docs",
            "completed_steps": ["reviewer"],
            "review_result": {"overall_score": 70, "verdict": "approve"},
        }


async def docs_node(state: WorkflowState) -> dict:
    from app.agents.docs import run_docs_agent
    try:
        result = await run_docs_agent(
            generated_code=state.get("codegen_result", {}),
            repo_analysis=state.get("analysis_result", {}),
            task_description=state["task_description"],
        )
        return {
            "docs_result": result,
            "current_agent": "human_approval",
            "completed_steps": ["docs"],
            "logs": [{"agent": "docs", "status": "completed", "message": "Documentation generated"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "docs", "error": str(e)}],
            "logs": [{"agent": "docs", "status": "error", "message": str(e)}],
            "current_agent": "human_approval",
            "completed_steps": ["docs"],
            "docs_result": {},
        }


async def human_approval_node(state: WorkflowState) -> dict:
    """Pause for human review — in LangGraph this is an interrupt point."""
    return {
        "current_agent": "github",
        "status": "awaiting_approval",
        "logs": [{"agent": "human_approval", "status": "waiting", "message": "Awaiting human approval before creating PR"}],
    }


async def github_node(state: WorkflowState) -> dict:
    from app.agents.github_agent import run_github_agent
    try:
        result = await run_github_agent(
            owner=state.get("owner", ""),
            repo=state.get("repo", ""),
            task_description=state["task_description"],
            generated_code=state.get("codegen_result", {}),
            plan=state.get("plan", {}),
            review_result=state.get("review_result", {}),
            docs_result=state.get("docs_result", {}),
            github_token=state.get("github_token"),
            simulate=not bool(state.get("github_token")),
        )
        return {
            "github_result": result,
            "current_agent": "completed",
            "completed_steps": ["github"],
            "status": "completed",
            "logs": [{"agent": "github", "status": "completed", "message": f"PR {'simulated' if result.get('simulated') else 'created'}: {result.get('pr_url', 'N/A')}"}],
        }
    except Exception as e:
        return {
            "errors": [{"agent": "github", "error": str(e)}],
            "logs": [{"agent": "github", "status": "error", "message": str(e)}],
            "completed_steps": ["github"],
            "status": "failed",
            "github_result": {},
        }


# ─── Conditional Edges ────────────────────────────────────────────────────────

def route_after_review(state: WorkflowState) -> str:
    """Skip docs if not needed, or go to docs."""
    wtype = state.get("workflow_type", "full")
    if wtype == "code_review":
        return "human_approval"
    return "docs"


def route_after_human_approval(state: WorkflowState) -> str:
    """Route based on human approval decision."""
    if state.get("human_approved", False):
        return "github"
    return END


# ─── Build Graph ──────────────────────────────────────────────────────────────

def build_workflow_graph() -> StateGraph:
    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("planner", planner_node)
    graph.add_node("codegen", codegen_node)
    graph.add_node("refactor", refactor_node)
    graph.add_node("testing", testing_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("docs", docs_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("github", github_node)

    # Entry point
    graph.set_entry_point("analyzer")

    # Linear edges
    graph.add_edge("analyzer", "knowledge")
    graph.add_edge("knowledge", "planner")
    graph.add_edge("planner", "codegen")
    graph.add_edge("codegen", "refactor")
    graph.add_edge("refactor", "testing")
    graph.add_edge("testing", "reviewer")

    # Conditional after reviewer
    graph.add_conditional_edges("reviewer", route_after_review, {
        "docs": "docs",
        "human_approval": "human_approval",
    })

    graph.add_edge("docs", "human_approval")

    # Conditional after human approval
    graph.add_conditional_edges("human_approval", route_after_human_approval, {
        "github": "github",
        END: END,
    })

    graph.add_edge("github", END)

    return graph


# Compiled graph with in-memory checkpointer (swap for Redis/Postgres in prod)
memory = MemorySaver()
workflow_graph = build_workflow_graph().compile(
    checkpointer=memory,
    interrupt_before=["human_approval"],
)
