"""
Planner Agent — receives a task description and decomposes it into
a structured execution plan with sub-tasks assigned to specific agents.
"""
import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm_service import get_llm

SYSTEM_PROMPT = """You are a senior software engineering lead AI. You receive a task request and a repository analysis, 
and you create a detailed execution plan for a team of specialized AI agents.

Available agents:
- analyzer: Analyzes repository structure and architecture
- knowledge: Searches code knowledge base semantically
- codegen: Generates new code (classes, functions, APIs)
- refactor: Refactors and improves existing code
- testing: Writes unit and integration tests
- reviewer: Reviews code for quality, security, performance
- docs: Generates documentation, README, UML diagrams
- github: Creates branches, commits, and pull requests

Return a JSON object with:
{
  "task_summary": "brief description of what needs to be done",
  "steps": [
    {
      "step": 1,
      "agent": "agent_name",
      "action": "specific action description",
      "input": "what data this step needs",
      "output": "what this step should produce",
      "depends_on": []
    }
  ],
  "estimated_duration_minutes": number,
  "complexity": "low|medium|high",
  "agents_required": ["list", "of", "agent", "names"],
  "risk_assessment": "brief risk notes",
  "success_criteria": "how to know if the task succeeded"
}

Return ONLY valid JSON."""


async def run_planner_agent(
    task_description: str,
    repo_analysis: dict[str, Any],
    workflow_type: str = "full",
) -> dict[str, Any]:
    """
    Decompose a developer task into a multi-agent execution plan.

    Args:
        task_description: Natural language task (e.g. "Fix the login bug")
        repo_analysis: Analysis result from analyzer agent
        workflow_type: Type of workflow

    Returns:
        Structured plan dict
    """
    llm = get_llm(temperature=0.2)

    context = f"""
Task: {task_description}
Workflow Type: {workflow_type}

Repository Analysis:
- Language: {repo_analysis.get('language', 'Unknown')}
- Framework: {repo_analysis.get('framework', 'Unknown')}
- Architecture: {repo_analysis.get('architecture_pattern', 'Unknown')}
- Tech Stack: {', '.join(repo_analysis.get('tech_stack', []))}
- Complexity Score: {repo_analysis.get('complexity_score', 5)}/10
- Services: {', '.join(repo_analysis.get('services', [])[:5])}
- APIs: {', '.join(repo_analysis.get('apis', [])[:5])}
- Issues Detected: {', '.join(repo_analysis.get('issues_detected', [])[:3])}
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Create an execution plan for:\n{context}"),
    ]

    response = await llm.ainvoke(messages)
    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    try:
        plan = json.loads(content)
    except json.JSONDecodeError:
        plan = {
            "task_summary": task_description,
            "steps": [
                {"step": 1, "agent": "analyzer", "action": "Analyze repository", "input": "repo_data", "output": "analysis", "depends_on": []},
                {"step": 2, "agent": "knowledge", "action": "Build knowledge base", "input": "file_contents", "output": "embeddings", "depends_on": [1]},
                {"step": 3, "agent": "codegen", "action": "Generate solution code", "input": "analysis + task", "output": "code_changes", "depends_on": [2]},
                {"step": 4, "agent": "testing", "action": "Write tests for changes", "input": "code_changes", "output": "test_files", "depends_on": [3]},
                {"step": 5, "agent": "reviewer", "action": "Review all changes", "input": "code_changes + tests", "output": "review_report", "depends_on": [4]},
                {"step": 6, "agent": "docs", "action": "Update documentation", "input": "code_changes", "output": "updated_docs", "depends_on": [3]},
                {"step": 7, "agent": "github", "action": "Create pull request", "input": "all_changes", "output": "pull_request", "depends_on": [5, 6]},
            ],
            "estimated_duration_minutes": 15,
            "complexity": "medium",
            "agents_required": ["analyzer", "knowledge", "codegen", "testing", "reviewer", "docs", "github"],
            "risk_assessment": "Standard workflow risk",
            "success_criteria": "All agents complete and PR is created",
        }

    return plan
