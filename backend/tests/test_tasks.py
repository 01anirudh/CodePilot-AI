import uuid


def test_agent_run_and_task_lifecycle(client):
    # 1. Create a project first
    project_payload = {
        "name": "fastapi-demo",
        "github_url": "https://github.com/demo/fastapi-demo",
        "description": "Demo project"
    }
    proj_res = client.post("/api/projects", json=project_payload)
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 2. Run agent task
    task_payload = {
        "project_id": project_id,
        "task": "Add user authentication and rate limiting",
        "workflow_type": "full"
    }
    run_res = client.post("/api/agents/run", json=task_payload)
    assert run_res.status_code == 202
    run_data = run_res.json()
    assert "task_id" in run_data
    assert run_data["status"] == "QUEUED"
    assert run_data["current_agent"] == "supervisor"
    task_id = run_data["task_id"]

    # 3. Query task details (structured state)
    task_res = client.get(f"/api/tasks/{task_id}")
    assert task_res.status_code == 200
    task_data = task_res.json()
    assert task_data["task_id"] == task_id
    assert "status" in task_data
    assert "current_agent" in task_data
    assert "iteration" in task_data
    assert isinstance(task_data["plan"], list)
    assert isinstance(task_data["tool_results"], list)
    assert isinstance(task_data["errors"], list)
    assert isinstance(task_data["files_changed"], list)
    assert isinstance(task_data["messages"], list)

    # 4. Query task status endpoint
    status_res = client.get(f"/api/tasks/{task_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["task_id"] == task_id
    assert status_data["status"] == "QUEUED"
    assert "completed" in status_data

    # 5. Approve task
    approve_res = client.post(
        f"/api/tasks/{task_id}/approve",
        json={"approved": True, "comment": "Approved by reviewer"}
    )
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["status"] in ["CODING", "RUNNING"]


def test_invalid_task_id(client):
    fake_id = str(uuid.uuid4())
    res = client.get(f"/api/tasks/{fake_id}")
    assert res.status_code == 404
