"""
Code Generation Agent — generates new code (classes, functions, APIs, SQL)
based on task description and repository context.
"""
import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm_service import get_llm

SYSTEM_PROMPT = """You are an expert software engineer. Generate production-quality code based on the task description and repository context.

Return a JSON object with:
{
  "files": [
    {
      "path": "relative/file/path.py",
      "action": "create|modify|delete",
      "content": "full file content here",
      "description": "what was changed and why"
    }
  ],
  "summary": "overall summary of changes made",
  "dependencies_added": ["new packages if any"],
  "breaking_changes": false,
  "migration_required": false
}

Follow these principles:
- Write clean, well-commented, idiomatic code
- Follow the repository's existing coding style
- Include proper error handling
- Write type hints for Python, TypeScript types for JS/TS
- Keep functions small and focused (single responsibility)

Return ONLY valid JSON."""


async def run_codegen_agent(
    task_description: str,
    plan_step: dict[str, Any],
    repo_analysis: dict[str, Any],
    relevant_code: list[dict] = None,
) -> dict[str, Any]:
    """
    Generate code changes based on task and plan.

    Args:
        task_description: The developer's original request
        plan_step: The specific plan step for code generation
        repo_analysis: Repository analysis output
        relevant_code: Semantically similar code snippets from knowledge base

    Returns:
        Dict with file changes
    """
    llm = get_llm(temperature=0.2)

    context_code = ""
    if relevant_code:
        snippets = [f"// {r['payload'].get('file_path', '')}\n{r['payload'].get('content', '')}" for r in relevant_code[:3]]
        context_code = "\n\n---\n".join(snippets)

    prompt = f"""Task: {task_description}

Repository Context:
- Language: {repo_analysis.get('language', 'Unknown')}
- Framework: {repo_analysis.get('framework', 'Unknown')}
- Architecture: {repo_analysis.get('architecture_pattern', 'Unknown')}

Action Required: {plan_step.get('action', 'Generate code')}
Expected Output: {plan_step.get('output', 'Code files')}

Relevant Existing Code:
{context_code or 'No relevant code found in knowledge base.'}

Generate the required code changes."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)
    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {
            "files": [],
            "summary": f"Code generation for: {task_description}",
            "dependencies_added": [],
            "breaking_changes": False,
            "migration_required": False,
            "raw_response": content,
        }

    return result
