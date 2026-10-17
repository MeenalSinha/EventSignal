"""Tests for user registration, authentication, tokens, and credentials."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.auth import (
    AuthenticationError,
    UserAlreadyExistsError,
    authenticate_user,
    register_user,
)


def test_password_hashing_and_verification() -> None:
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password, "invalid_hash_string") is False


def test_access_token_creation_and_validation() -> None:
    secret = "test-secret-key-for-tokens-12345"
    token = create_access_token(
        subject="user-123",
        secret_key=secret,
        expires_in_seconds=3600,
        claims={"email": "student@iiitd.ac.in"},
    )
    payload = decode_access_token(token, secret)

    assert payload["sub"] == "user-123"
    assert payload["email"] == "student@iiitd.ac.in"
    assert "exp" in payload

    # Tampered signature should fail
    tampered = token[:-4] + "abcd"
    with pytest.raises(ValueError, match="Invalid token signature"):
        decode_access_token(tampered, secret)

    # Wrong secret should fail
    with pytest.raises(ValueError, match="Invalid token signature"):
        decode_access_token(token, "different-secret-key")

    # Expired token should fail
    expired_token = create_access_token(
        subject="user-old",
        secret_key=secret,
        expires_in_seconds=-10,
    )
    with pytest.raises(ValueError, match="Token has expired"):
        decode_access_token(expired_token, secret)


def test_user_registration_and_auth_service(session) -> None:
    user = register_user(
        session=session,
        email="student1@iiitd.ac.in",
        password="ValidPassword123!",
        full_name="Alice Sharma",
    )
    assert user.id is not None
    assert user.email == "student1@iiitd.ac.in"
    assert user.full_name == "Alice Sharma"
    assert user.is_active is True

    # Duplicate registration should raise UserAlreadyExistsError
    with pytest.raises(UserAlreadyExistsError):
        register_user(
            session=session,
            email="STUDENT1@iiitd.ac.in",
            password="AnotherPassword123!",
            full_name="Alice Duplicate",
        )

    # Successful authentication
    authenticated = authenticate_user(
        session=session,
        email="student1@iiitd.ac.in",
        password="ValidPassword123!",
    )
    assert authenticated.id == user.id

    # Failed authentication (wrong password)
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        authenticate_user(
            session=session,
            email="student1@iiitd.ac.in",
            password="WrongPassword!",
        )

    # Failed authentication (unknown user)
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        authenticate_user(
            session=session,
            email="unknown@iiitd.ac.in",
            password="ValidPassword123!",
        )


def test_auth_api_flow(client: TestClient) -> None:
    # 1. Register
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alumni1@iiitd.ac.in",
            "password": "SecurePassword123!",
            "full_name": "Rohan Gupta",
        },
    )
    assert reg_resp.status_code == 201
    token_data = reg_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "Bearer"
    token = token_data["access_token"]

    # 2. Duplicate registration gives 409 Conflict
    dup_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alumni1@iiitd.ac.in",
            "password": "SecurePassword123!",
            "full_name": "Rohan Gupta",
        },
    )
    assert dup_resp.status_code == 409

    # 3. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "alumni1@iiitd.ac.in",
            "password": "SecurePassword123!",
        },
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 4. Login with bad password gives 401
    bad_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "alumni1@iiitd.ac.in",
            "password": "WrongPassword123!",
        },
    )
    assert bad_login.status_code == 401

    # 5. /api/v1/auth/me without token gives 401
    unauth_resp = client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401

    # 6. /api/v1/auth/me with valid Bearer token gives 200
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["user"]["email"] == "alumni1@iiitd.ac.in"
    assert me_data["user"]["full_name"] == "Rohan Gupta"
    assert isinstance(me_data["memberships"], list)
