"""
Documentation Agent — generates README, API docs, UML diagrams, and sequence diagrams.
"""
import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm_service import get_llm

SYSTEM_PROMPT = """You are a technical writer and documentation expert. Generate comprehensive documentation.

Return a JSON object with:
{
  "readme": "full README.md markdown content",
  "api_docs": "API documentation in markdown",
  "uml_diagram": "PlantUML class diagram code",
  "sequence_diagram": "PlantUML sequence diagram for main flow",
  "changelog_entry": "CHANGELOG.md entry for these changes",
  "inline_comments": [
    {
      "file": "file path",
      "additions": [{"line": number, "comment": "comment to add"}]
    }
  ],
  "summary": "documentation summary"
}

Return ONLY valid JSON."""


async def run_docs_agent(
    generated_code: dict[str, Any],
    repo_analysis: dict[str, Any],
    task_description: str,
) -> dict[str, Any]:
    """
    Generate documentation for the changes.

    Args:
        generated_code: Output from codegen agent
        repo_analysis: Repository analysis
        task_description: Original task

    Returns:
        Documentation artifacts
    """
    llm = get_llm(temperature=0.3)

    files_summary = "\n".join(
        [f"- {f['path']}: {f.get('description', 'Modified')}"
         for f in generated_code.get("files", [])[:5]]
    )

    prompt = f"""Generate documentation for these changes to a {repo_analysis.get('language', '')} {repo_analysis.get('framework', '')} project.

Task implemented: {task_description}

Files changed:
{files_summary or 'No files listed.'}

Architecture: {repo_analysis.get('architecture_pattern', 'Unknown')}
Services: {', '.join(repo_analysis.get('services', [])[:5])}

Generate complete documentation including README updates, API docs, and UML diagrams."""

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
            "readme": f"# Changes\n\n{task_description}\n\n## Files Modified\n\n{files_summary}",
            "api_docs": "API documentation pending",
            "uml_diagram": "@startuml\n' UML diagram\n@enduml",
            "sequence_diagram": "@startuml\n' Sequence diagram\n@enduml",
            "changelog_entry": f"## Changes\n\n- {task_description}",
            "inline_comments": [],
            "summary": "Documentation generated",
            "raw_response": content,
        }

    return result
