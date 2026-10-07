"""
Supervisor Agent - Orchestrates the workflow by deciding which agent to run next based on state.
"""
import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm_service import get_llm

SYSTEM_PROMPT = """You are the Supervisor Agent overseeing a software development workflow.
You manage a team of specialized agents:
- analyzer: Analyzes repository structure and architecture
- knowledge: Searches code knowledge base semantically
- planner: Creates execution plans for tasks
- codegen: Generates new code and modifies existing code
- refactor: Refactors and improves code quality
- testing: Writes unit and integration tests
- reviewer: Reviews code for quality, security, performance
- docs: Generates documentation
- human_approval: Pauses for human review before deployment
- github: Creates branches, commits, and pull requests

Your job is to determine the next agent to run based on the current state, completed steps, human approval status, and any errors.
If the task is fully complete, return "finish".

Respond ONLY with a JSON object matching this schema:
{
  "next": "analyzer" | "knowledge" | "planner" | "codegen" | "refactor" | "testing" | "reviewer" | "docs" | "human_approval" | "github" | "finish",
  "reason": "Brief explanation of why this agent is next"
}
"""

async def run_supervisor_agent(
    task_description: str,
    completed_steps: list[str],
    current_plan: dict[str, Any],
    errors: list[dict[str, Any]],
    human_approved: bool = False,
    workflow_type: str = "full"
) -> dict[str, Any]:
    from app.config import settings
    if len(completed_steps) >= settings.AGENT_MAX_ITERATIONS:
        return {
            "next": "finish",
            "reason": f"Reached maximum iteration limit of {settings.AGENT_MAX_ITERATIONS}"
        }

    def _fallback_routing() -> dict[str, Any]:
        """Deterministic agent pipeline fallback when LLM is unavailable."""
        pipeline_map = {
            "analyze": ["analyzer"],
            "code_review": ["analyzer", "reviewer"],
            "generate_tests": ["analyzer", "testing", "reviewer"],
            "generate_docs": ["analyzer", "docs"],
            "refactor": ["analyzer", "refactor", "testing", "reviewer"],
            "bug_fix": ["analyzer", "knowledge", "planner", "codegen", "testing", "reviewer", "human_approval", "github"],
            "full": ["analyzer", "knowledge", "planner", "codegen", "refactor", "testing", "reviewer", "docs", "human_approval", "github"],
        }
        steps = pipeline_map.get(workflow_type, pipeline_map["full"])
        for step in steps:
            if step not in completed_steps:
                if step == "human_approval" and not human_approved:
                    return {"next": "human_approval", "reason": "Awaiting human approval before PR"}
                if step == "github" and not human_approved:
                    return {"next": "human_approval", "reason": "Requires human approval before GitHub operations"}
                return {"next": step, "reason": f"Deterministic next step: {step}"}
        return {"next": "finish", "reason": "All pipeline steps completed"}

    try:
        llm = get_llm(temperature=0.1)
        
        context = f"""
Task: {task_description}
Workflow Type: {workflow_type}
Completed Steps: {', '.join(completed_steps) if completed_steps else 'None'}
Human Approved: {human_approved}
Errors: {json.dumps(errors) if errors else 'None'}
"""
        if current_plan and "steps" in current_plan:
            context += f"\nCurrent Plan Steps: {json.dumps([s.get('agent') for s in current_plan.get('steps', [])])}"

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Determine the next agent for the following state:\n{context}")
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
                
        result = json.loads(content)
        valid_agents = ["analyzer", "knowledge", "planner", "codegen", "refactor", "testing", "reviewer", "docs", "human_approval", "github", "finish"]
        if result.get("next") not in valid_agents:
            return _fallback_routing()
            
        # Ensure human approval is respected even if LLM tries to skip it
        if result.get("next") == "github" and not human_approved and "human_approval" not in completed_steps:
            return {"next": "human_approval", "reason": "Safety check: human approval required before PR"}
            
        return result
    except Exception:
        return _fallback_routing()