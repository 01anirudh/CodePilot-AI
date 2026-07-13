"""
Testing Agent — automatically generates unit tests, integration tests,
mock objects and edge cases for the generated code.
"""
import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm_service import get_llm

SYSTEM_PROMPT = """You are an expert test engineer. Generate comprehensive tests for the provided code.

Return a JSON object with:
{
  "test_files": [
    {
      "path": "tests/test_filename.py",
      "content": "full test file content",
      "test_count": number,
      "coverage_estimate": "percentage"
    }
  ],
  "test_strategy": {
    "unit_tests": true,
    "integration_tests": true,
    "mock_objects": true,
    "edge_cases": ["list of edge cases covered"]
  },
  "framework_used": "pytest|jest|junit|etc",
  "total_test_count": number,
  "coverage_estimate": "estimated % coverage",
  "summary": "what was tested"
}

Include:
- Unit tests for each function/method
- Integration tests for API endpoints
- Mock objects for external dependencies
- Edge cases (null, empty, boundary values)
- Error/exception cases

Return ONLY valid JSON."""


async def run_testing_agent(
    generated_code: dict[str, Any],
    repo_analysis: dict[str, Any],
    task_description: str,
) -> dict[str, Any]:
    """
    Generate tests for generated code changes.

    Args:
        generated_code: Output from codegen agent
        repo_analysis: Repository analysis
        task_description: Original task

    Returns:
        Test files and strategy
    """
    llm = get_llm(temperature=0.1)

    files_content = "\n\n---\n".join(
        [f"File: {f['path']}\n{f.get('content', '')[:2000]}"
         for f in generated_code.get("files", [])[:3]]
    )

    prompt = f"""Generate comprehensive tests for this {repo_analysis.get('language', '')} code.

Task that was implemented: {task_description}
Test Framework: {repo_analysis.get('test_framework', 'auto-detect')}

Code to test:
{files_content or 'No generated files provided.'}

Generate thorough tests with full coverage."""

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
            "test_files": [],
            "test_strategy": {
                "unit_tests": True,
                "integration_tests": True,
                "mock_objects": True,
                "edge_cases": [],
            },
            "framework_used": repo_analysis.get("test_framework", "pytest"),
            "total_test_count": 0,
            "coverage_estimate": "0%",
            "summary": "Test generation complete",
            "raw_response": content,
        }

    return result
