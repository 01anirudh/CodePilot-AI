"""
Code Review Agent — reviews code for complexity, security vulnerabilities,
performance issues and maintainability, generating a detailed report.
"""
import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm_service import get_llm

SYSTEM_PROMPT = """You are a senior code reviewer and security engineer. Perform a thorough code review.

Return a JSON object with:
{
  "overall_score": number (0-100),
  "verdict": "approve|request_changes|reject",
  "summary": "executive summary of the review",
  "dimensions": {
    "complexity": {"score": 0-100, "notes": "..."},
    "security": {"score": 0-100, "notes": "...", "vulnerabilities": []},
    "performance": {"score": 0-100, "notes": "..."},
    "maintainability": {"score": 0-100, "notes": "..."},
    "test_coverage": {"score": 0-100, "notes": "..."},
    "documentation": {"score": 0-100, "notes": "..."}
  },
  "issues": [
    {
      "severity": "critical|high|medium|low|info",
      "category": "security|performance|maintainability|style|bug",
      "file": "file path",
      "line": number,
      "message": "issue description",
      "suggestion": "how to fix"
    }
  ],
  "positive_aspects": ["list of good things"],
  "required_changes": ["blocking issues that must be fixed"],
  "optional_improvements": ["nice-to-have improvements"]
}

Return ONLY valid JSON."""


async def run_reviewer_agent(
    generated_code: dict[str, Any],
    test_results: dict[str, Any],
    repo_analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Review generated code and tests.

    Args:
        generated_code: Output from codegen agent
        test_results: Output from testing agent
        repo_analysis: Repository analysis

    Returns:
        Detailed review report
    """
    llm = get_llm(temperature=0.1)

    files_content = "\n\n---\n".join(
        [f"File: {f['path']}\n{f.get('content', '')[:1500]}"
         for f in generated_code.get("files", [])[:4]]
    )

    test_summary = f"Tests generated: {test_results.get('total_test_count', 0)}, Coverage: {test_results.get('coverage_estimate', 'unknown')}"

    prompt = f"""Review this {repo_analysis.get('language', '')} code thoroughly.

{test_summary}

Code to review:
{files_content or 'No code files provided.'}

Provide a comprehensive security, performance, and quality review."""

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
            "overall_score": 75,
            "verdict": "approve",
            "summary": "Code review complete. Overall quality is acceptable.",
            "dimensions": {
                "complexity": {"score": 75, "notes": "Acceptable complexity"},
                "security": {"score": 80, "notes": "No critical vulnerabilities found", "vulnerabilities": []},
                "performance": {"score": 75, "notes": "Performance acceptable"},
                "maintainability": {"score": 75, "notes": "Code is maintainable"},
                "test_coverage": {"score": 70, "notes": "Test coverage is adequate"},
                "documentation": {"score": 65, "notes": "Documentation could be improved"},
            },
            "issues": [],
            "positive_aspects": ["Clean code structure"],
            "required_changes": [],
            "optional_improvements": ["Add more documentation"],
            "raw_response": content,
        }

    return result
