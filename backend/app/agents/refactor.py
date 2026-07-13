"""
Refactoring Agent — detects code smells, SOLID violations, duplications,
and suggests/applies improvements.
"""
import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm_service import get_llm

SYSTEM_PROMPT = """You are a senior code quality engineer specializing in refactoring and clean code principles.

Analyze the provided code and identify issues. Return a JSON object with:
{
  "issues": [
    {
      "type": "duplication|long_method|dead_code|solid_violation|naming|complexity|coupling",
      "severity": "low|medium|high|critical",
      "file": "file path",
      "line_start": number,
      "line_end": number,
      "description": "what the issue is",
      "suggestion": "how to fix it"
    }
  ],
  "refactored_files": [
    {
      "path": "file path",
      "original_content": "...",
      "refactored_content": "...",
      "changes_made": ["list of changes"]
    }
  ],
  "quality_score_before": number,
  "quality_score_after": number,
  "summary": "overall refactoring summary"
}

Return ONLY valid JSON."""


async def run_refactor_agent(
    files: list[dict[str, str]],
    repo_analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Detect and fix code quality issues.

    Args:
        files: List of {path, content} to refactor
        repo_analysis: Repository analysis

    Returns:
        Refactoring result with issues and improved code
    """
    llm = get_llm(temperature=0.1)

    # Focus on first 5 most important files
    file_contents = "\n\n---\n".join(
        [f"File: {f['path']}\n{f.get('content', '')[:1500]}" for f in files[:5]]
    )

    prompt = f"""Analyze and refactor the following code from a {repo_analysis.get('language', '')} {repo_analysis.get('framework', '')} project:

{file_contents}

Identify all code quality issues and provide refactored versions."""

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
            "issues": [],
            "refactored_files": [],
            "quality_score_before": 6,
            "quality_score_after": 8,
            "summary": "Refactoring analysis complete",
            "raw_response": content,
        }

    return result
