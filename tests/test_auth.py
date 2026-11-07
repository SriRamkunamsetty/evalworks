from evalworks.auth import hash_password
from evalworks.models import User, Workspace


def create_user(db, *, workspace_id="local", email="reviewer@example.com", role="reviewer"):
    user = User(
        workspace_id=workspace_id,
        email=email,
        password_hash=hash_password("a-strong-test-password-123"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def login(client, email):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "a-strong-test-password-123"},
    )


def add_user(client, **kwargs):
    with client.app.state.test_session() as db:
        return create_user(db, **kwargs)


def test_login_sets_http_only_session_and_me_returns_workspace(client):
    user = add_user(client)
    response = login(client, user.email)

    assert response.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()
    assert client.get("/api/v1/auth/me").json() == {
        "id": user.id,
        "email": user.email,
        "role": "reviewer",
        "workspace_id": "local",
    }


def test_cookie_session_requires_csrf_for_mutations(client):
    user = add_user(client)
    assert login(client, user.email).status_code == 200
    payload = {"payload": {"human_score": 3, "judge_score": 3, "scale": 5}}

    denied = client.post("/api/v1/projects/judgebench/evaluate", json=payload)
    assert denied.status_code == 403

    csrf = client.cookies.get("ew_csrf")
    allowed = client.post(
        "/api/v1/projects/judgebench/evaluate",
        json=payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert allowed.status_code == 201


def test_workspace_isolation_and_viewer_permissions(client):
    with client.app.state.test_session() as db:
        second = Workspace(name="Second workspace")
        db.add(second)
        db.commit()
        second_workspace_id = second.id
    first_user = add_user(client, email="first@example.com")
    second_user = add_user(
        client, workspace_id=second_workspace_id, email="second@example.com", role="viewer"
    )

    assert login(client, first_user.email).status_code == 200
    run = client.post(
        "/api/v1/projects/judgebench/evaluate",
        json={"payload": {"human_score": 4, "judge_score": 4, "scale": 5}},
        headers={"X-CSRF-Token": client.cookies.get("ew_csrf")},
    ).json()
    assert (
        client.post(
            "/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("ew_csrf")}
        ).status_code
        == 200
    )

    assert login(client, second_user.email).status_code == 200
    assert client.get(f"/api/v1/runs/{run['id']}").status_code == 404
    assert client.get("/api/v1/runs").json() == []
    blocked = client.post(
        "/api/v1/projects/judgebench/evaluate",
        json={"payload": {"human_score": 4, "judge_score": 4, "scale": 5}},
        headers={"X-CSRF-Token": client.cookies.get("ew_csrf")},
    )
    assert blocked.status_code == 403


def test_login_rejects_invalid_credentials_without_leaking_account_state(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email or password is incorrect"


def test_logout_clears_session(client):
    user = add_user(client)
    assert login(client, user.email).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200
    assert (
        client.post(
            "/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("ew_csrf")}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/auth/me").status_code == 401


def test_admin_can_provision_workspace_member_but_viewer_cannot(client):
    admin = add_user(client, email="admin@example.com", role="admin")
    assert login(client, admin.email).status_code == 200
    created = client.post(
        "/api/v1/users",
        json={
            "email": "new-reviewer@example.com",
            "password": "a-strong-test-password-123",
            "role": "reviewer",
        },
        headers={"X-CSRF-Token": client.cookies.get("ew_csrf")},
    )
    assert created.status_code == 201
    assert created.json()["role"] == "reviewer"
    assert [user["email"] for user in client.get("/api/v1/users").json()] == [
        "admin@example.com",
        "new-reviewer@example.com",
    ]

    assert (
        client.post(
            "/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("ew_csrf")}
        ).status_code
        == 200
    )
    viewer = add_user(client, email="viewer@example.com", role="viewer")
    assert login(client, viewer.email).status_code == 200
    denied = client.post(
        "/api/v1/users",
        json={
            "email": "other@example.com",
            "password": "a-strong-test-password-123",
            "role": "reviewer",
        },
        headers={"X-CSRF-Token": client.cookies.get("ew_csrf")},
    )
    assert denied.status_code == 403
    assert client.get("/api/v1/users").status_code == 403
