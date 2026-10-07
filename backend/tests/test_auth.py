def test_register_and_login_flow(client):
    # 1. Register
    reg_payload = {
        "email": "testdev@example.com",
        "username": "testdev",
        "full_name": "Test Developer",
        "password": "Password123!"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "testdev@example.com"
    assert user_data["username"] == "testdev"

    # 2. Login
    login_data = {
        "username": "testdev@example.com",
        "password": "Password123!"
    }
    login_res = client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 3. Get /me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "testdev"
