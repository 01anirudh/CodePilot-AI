"""
Repository Analyzer Agent — reads folder structure, detects frameworks,
identifies dependencies, and builds an architecture map.
"""
import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.llm_service import get_llm

SYSTEM_PROMPT = """You are a senior software architect. Analyze the provided repository structure and metadata.

Extract and return a JSON object with:
- language: primary programming language
- framework: main framework(s) detected
- architecture_pattern: (MVC, microservices, monolith, etc.)
- services: list of detected services/modules
- apis: list of detected API endpoints or controllers
- dependencies: key external dependencies
- folder_structure_summary: brief description of the repo layout
- complexity_score: 1-10 score of code complexity
- tech_stack: array of all technologies detected
- entry_points: main entry files
- test_framework: testing framework if present
- ci_cd: CI/CD configuration detected
- issues_detected: list of potential issues or code smells noticed
- recommendations: top 3 architectural recommendations

Return ONLY valid JSON."""


async def run_analyzer_agent(
    repo_data: dict[str, Any],
    tree: list[dict],
    readme: str = "",
) -> dict[str, Any]:
    """
    Analyze a repository and return structured architectural information.

    Args:
        repo_data: GitHub API repository metadata
        tree: File tree from GitHub API
        readme: README content

    Returns:
        Structured analysis result dict
    """
    llm = get_llm(temperature=0.1)

    # Build context
    file_paths = [item["path"] for item in tree if item.get("type") == "blob"]
    context = f"""
        Repository: {repo_data.get('full_name', 'unknown')}
        Description: {repo_data.get('description', 'N/A')}
        Primary Language: {repo_data.get('language', 'Unknown')}
        Stars: {repo_data.get('stargazers_count', 0)}
        Default Branch: {repo_data.get('default_branch', 'main')}

        File Tree (first 200 files):
        {chr(10).join(file_paths[:200])}

        README (first 2000 chars):
        {readme[:2000]}
        """

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze this repository:\n{context}"),
    ]

    response = await llm.ainvoke(messages)
    content = response.content.strip()

    # Clean up markdown code fences if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Fallback structured result
        result = {
            "language": repo_data.get("language", "Unknown"),
            "framework": "Unknown",
            "architecture_pattern": "Unknown",
            "services": [],
            "apis": [],
            "dependencies": [],
            "folder_structure_summary": "Analysis in progress",
            "complexity_score": 5,
            "tech_stack": [repo_data.get("language", "Unknown")],
            "entry_points": [],
            "test_framework": None,
            "ci_cd": None,
            "issues_detected": [],
            "recommendations": [],
            "raw_response": content,
        }

    return result
