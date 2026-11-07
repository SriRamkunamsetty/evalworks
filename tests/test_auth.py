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


def login(client, email, otp=None):
    credentials = {"email": email, "password": "a-strong-test-password-123"}
    if otp is not None:
        credentials["otp"] = otp
    return client.post(
        "/api/v1/auth/login",
        json=credentials,
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


def test_totp_mfa_recovery_codes_are_single_use_and_can_be_disabled(client):
    import pyotp

    user = add_user(client, email="mfa@example.com")
    assert login(client, user.email).status_code == 200
    csrf = {"X-CSRF-Token": client.cookies.get("ew_csrf")}
    setup = client.post(
        "/api/v1/auth/mfa/setup",
        json={"password": "a-strong-test-password-123"},
        headers=csrf,
    )
    assert setup.status_code == 200
    secret = setup.json()["manual_secret"]

    confirmed = client.post(
        "/api/v1/auth/mfa/confirm",
        json={"code": pyotp.TOTP(secret).now()},
        headers=csrf,
    )
    assert confirmed.status_code == 200
    recovery_code = confirmed.json()["recovery_codes"][0]
    assert (
        client.post(
            "/api/v1/auth/mfa/setup",
            json={"password": "a-strong-test-password-123"},
            headers=csrf,
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/v1/auth/mfa/confirm",
            json={"code": pyotp.TOTP(secret).now()},
            headers=csrf,
        ).status_code
        == 409
    )
    assert len(confirmed.json()["recovery_codes"]) == 10
    assert len(recovery_code) == 32

    assert client.post("/api/v1/auth/logout", headers=csrf).status_code == 200
    assert login(client, user.email).status_code == 401
    assert login(client, user.email, recovery_code).status_code == 200
    csrf = {"X-CSRF-Token": client.cookies.get("ew_csrf")}
    assert client.post("/api/v1/auth/logout", headers=csrf).status_code == 200
    assert login(client, user.email, recovery_code).status_code == 401

    assert login(client, user.email, pyotp.TOTP(secret).now()).status_code == 200
    csrf = {"X-CSRF-Token": client.cookies.get("ew_csrf")}
    disabled = client.post(
        "/api/v1/auth/mfa/disable",
        json={"password": "a-strong-test-password-123", "code": pyotp.TOTP(secret).now()},
        headers=csrf,
    )
    assert disabled.status_code == 200
    assert disabled.json()["sessions_revoked"] is True
    assert client.get("/api/v1/auth/me").status_code == 401
    assert login(client, user.email).status_code == 200


def test_operator_password_recovery_revokes_sessions_and_can_clear_lost_mfa(client, monkeypatch):
    import pyotp

    from evalworks import cli
    from evalworks.auth import verify_password
    from evalworks.crypto import encrypt_secret

    user = add_user(client, email="recovery@example.com", role="admin")
    secret = pyotp.random_base32()
    with client.app.state.test_session() as db:
        db_user = db.get(User, user.id)
        db_user.mfa_enabled = True
        db_user.mfa_secret_ciphertext = encrypt_secret(secret)
        version = db_user.session_version
        db.commit()

    assert login(client, user.email, pyotp.TOTP(secret).now()).status_code == 200

    passwords = iter(["recovered-account-password-123", "recovered-account-password-123"])
    monkeypatch.setattr(cli, "getpass", lambda _prompt: next(passwords))
    cli.reset_password(user.email, disable_mfa=True, session_factory=client.app.state.test_session)
    assert client.get("/api/v1/auth/me").status_code == 401
    with client.app.state.test_session() as db:
        updated = db.get(User, user.id)
        assert updated.session_version == version + 1
        assert updated.mfa_enabled is False
        assert verify_password("recovered-account-password-123", updated.password_hash)
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": "recovered-account-password-123"},
        ).status_code
        == 200
    )
