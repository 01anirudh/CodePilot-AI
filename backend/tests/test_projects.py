def test_create_and_list_projects(client):
    payload = {
        "name": "test-repo",
        "github_url": "https://github.com/testowner/test-repo",
        "description": "A test repository for unit testing"
    }
    response = client.post("/api/projects", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-repo"
    assert data["full_name"] == "testowner/test-repo"
    assert data["github_url"] == payload["github_url"]
    assert "id" in data

    # List projects
    list_res = client.get("/api/projects")
    assert list_res.status_code == 200
    projects = list_res.json()
    assert len(projects) >= 1
    assert any(p["name"] == "test-repo" for p in projects)
