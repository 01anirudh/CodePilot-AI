import pytest
from app.agents.supervisor import run_supervisor_agent


@pytest.mark.asyncio
async def test_supervisor_deterministic_fallback_sequence():
    # Sequence test for full pipeline
    step1 = await run_supervisor_agent(
        task_description="Fix authentication error",
        completed_steps=[],
        current_plan={},
        errors=[],
        human_approved=False,
        workflow_type="full"
    )
    assert step1["next"] == "analyzer"

    step2 = await run_supervisor_agent(
        task_description="Fix authentication error",
        completed_steps=["analyzer"],
        current_plan={},
        errors=[],
        human_approved=False,
        workflow_type="full"
    )
    assert step2["next"] == "knowledge"

    # Testing human approval pause
    step_pause = await run_supervisor_agent(
        task_description="Fix authentication error",
        completed_steps=["analyzer", "knowledge", "planner", "codegen", "refactor", "testing", "reviewer", "docs"],
        current_plan={},
        errors=[],
        human_approved=False,
        workflow_type="full"
    )
    assert step_pause["next"] == "human_approval"

    # Testing resumption after approval
    step_resume = await run_supervisor_agent(
        task_description="Fix authentication error",
        completed_steps=["analyzer", "knowledge", "planner", "codegen", "refactor", "testing", "reviewer", "docs", "human_approval"],
        current_plan={},
        errors=[],
        human_approved=True,
        workflow_type="full"
    )
    assert step_resume["next"] == "github"


@pytest.mark.asyncio
async def test_supervisor_iteration_limit():
    result = await run_supervisor_agent(
        task_description="Infinite loop task",
        completed_steps=["step1", "step2", "step3", "step4", "step5", "step6", "step7", "step8", "step9", "step10"],
        current_plan={},
        errors=[],
        human_approved=False,
        workflow_type="full"
    )
    assert result["next"] == "finish"
    assert "limit" in result.get("reason", "").lower()
