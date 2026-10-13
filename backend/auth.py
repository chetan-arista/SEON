"""Authentication primitives and OAuth2/OIDC routes for SEON."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import os
import re
import secrets
import urllib.parse
import urllib.request
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from backend import storage

router = APIRouter(prefix="/api/auth", tags=["authentication"])
SESSION_COOKIE = "seon_session"
SESSION_DAYS = 14
PBKDF2_ITERATIONS = 600_000
EMAIL_PATTERN = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,63}$")


def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        algorithm, rounds, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def public_user(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "display_name": user.get("display_name", ""), "role": user["role"]}


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_session(response: Response, user: dict) -> None:
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    storage.create_session(token_digest(token), user["id"], expires.isoformat())
    response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=os.getenv("SEON_COOKIE_SECURE", "false").lower() == "true",
                        samesite="lax", max_age=SESSION_DAYS * 86400, path="/")


def revoke_session(request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        storage.delete_session(token_digest(token))
    response.delete_cookie(SESSION_COOKIE, path="/")


def user_from_cookie(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token or len(token) > 256:
        return None
    return storage.user_for_session(token_digest(token))


def bootstrap_admin() -> None:
    email = os.getenv("SEON_ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("SEON_ADMIN_PASSWORD", "")
    if not email and not password:
        return
    if not email or not password or not EMAIL_PATTERN.fullmatch(email):
        raise RuntimeError("Set both SEON_ADMIN_EMAIL and SEON_ADMIN_PASSWORD to bootstrap the first administrator.")
    if len(password) < 12:
        raise RuntimeError("SEON_ADMIN_PASSWORD must be at least 12 characters.")
    existing = storage.find_user_by_email(email)
    if existing:
        # Environment bootstrap may promote the configured account, but it must
        # not silently reset its password on every API restart.
        if existing["role"] != "admin":
            storage.set_user_role(existing["id"], "admin")
        if not existing.get("password_hash"):
            storage.set_password(existing["id"], password_hash(password))
    else:
        storage.create_user(email, "SEON Administrator", "admin", password_hash(password))


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class Signup(Credentials):
    display_name: str = Field(min_length=1, max_length=160)


@router.get("/me")
async def me(request: Request) -> dict:
    user = user_from_cookie(request)
    if not user:
        raise HTTPException(401, "Sign in to continue.")
    return {"user": public_user(user)}


@router.post("/signup")
async def signup(body: Signup, response: Response) -> dict:
    email = body.email.strip().lower()
    if not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(422, "Enter a valid email address.")
    if len(body.password) < 12:
        raise HTTPException(422, "Use a password with at least 12 characters.")
    if storage.find_user_by_email(email):
        raise HTTPException(409, "An account with this email already exists. Sign in instead.")
    try:
        user = storage.create_user(email, body.display_name, "client", password_hash(body.password))
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            raise HTTPException(409, "An account with this email already exists. Sign in instead.") from None
        raise
    issue_session(response, user)
    return {"user": public_user(user)}


@router.post("/login")
async def login(body: Credentials, response: Response) -> dict:
    user = storage.find_user_by_email(body.email.strip().lower())
    if not user or user.get("disabled") or not verify_password(body.password, user.get("password_hash")):
        raise HTTPException(401, "Email or password is incorrect.")
    issue_session(response, user)
    return {"user": public_user(user)}


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict:
    revoke_session(request, response)
    return {"ok": True}


def oauth_config() -> tuple[str, str, str]:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(503, "Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, and GOOGLE_OAUTH_REDIRECT_URI.")
    return client_id, client_secret, redirect_uri


def frontend_url() -> str:
    return os.getenv("SEON_FRONTEND_URL", "http://localhost:5173").rstrip("/")


@router.get("/google/start")
async def google_start(response: Response) -> dict:
    client_id, _, redirect_uri = oauth_config()
    state, nonce, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    params = urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": "openid email profile", "state": state, "nonce": nonce,
        "code_challenge": challenge, "code_challenge_method": "S256", "prompt": "select_account",
    })
    secure = os.getenv("SEON_COOKIE_SECURE", "false").lower() == "true"
    for name, value in (("seon_oauth_state", state), ("seon_oauth_nonce", nonce), ("seon_oauth_verifier", verifier)):
        response.set_cookie(name, value, httponly=True, secure=secure, samesite="lax", max_age=600, path="/api/auth/google/callback")
    return {"authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?" + params}


def _exchange_code(code: str, client_id: str, client_secret: str, redirect_uri: str, verifier: str) -> dict:
    payload = urllib.parse.urlencode({"code": code, "client_id": client_id, "client_secret": client_secret,
                                     "redirect_uri": redirect_uri, "grant_type": "authorization_code",
                                     "code_verifier": verifier}).encode()
    request = urllib.request.Request("https://oauth2.googleapis.com/token", data=payload,
                                    headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read(100_000).decode())
    except Exception as exc:
        raise HTTPException(502, f"Google OAuth token exchange failed: {str(exc)[:160]}") from None


@router.get("/google/callback")
async def google_callback(request: Request) -> Response:
    state = request.query_params.get("state", "")
    code = request.query_params.get("code", "")
    cookies = request.cookies
    valid_state = state and cookies.get("seon_oauth_state") and hmac.compare_digest(state, cookies["seon_oauth_state"])
    if request.query_params.get("error") or not valid_state or not code:
        return RedirectResponse(f"{frontend_url()}/?auth_error=google_signin_failed", status_code=303)
    client_id, client_secret, redirect_uri = oauth_config()
    token_data = await asyncio.to_thread(_exchange_code, code, client_id, client_secret, redirect_uri, cookies.get("seon_oauth_verifier", ""))
    identity_token = token_data.get("id_token")
    if not identity_token:
        return RedirectResponse(f"{frontend_url()}/?auth_error=google_signin_failed", status_code=303)
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token
        claims = await asyncio.to_thread(id_token.verify_oauth2_token, identity_token, GoogleRequest(), client_id)
    except Exception:
        return RedirectResponse(f"{frontend_url()}/?auth_error=google_signin_failed", status_code=303)
    if claims.get("nonce") != cookies.get("seon_oauth_nonce") or claims.get("email_verified") is not True:
        return RedirectResponse(f"{frontend_url()}/?auth_error=google_signin_failed", status_code=303)
    subject = str(claims.get("sub", ""))
    email = str(claims.get("email", "")).strip().lower()
    if not subject or not EMAIL_PATTERN.fullmatch(email):
        return RedirectResponse(f"{frontend_url()}/?auth_error=google_signin_failed", status_code=303)
    user = storage.find_user_by_google_sub(subject)
    if not user:
        user = storage.find_user_by_email(email)
        if user:
            storage.link_google_sub(user["id"], subject)
            user = storage.get_user(user["id"])
        else:
            try:
                user = storage.create_user(email, str(claims.get("name", "")), "client", google_sub=subject)
            except Exception:
                user = storage.find_user_by_google_sub(subject)
    if not user or user.get("disabled"):
        return RedirectResponse(f"{frontend_url()}/?auth_error=account_unavailable", status_code=303)
    response = RedirectResponse(f"{frontend_url()}/", status_code=303)
    issue_session(response, user)
    for name in ("seon_oauth_state", "seon_oauth_nonce", "seon_oauth_verifier"):
        response.delete_cookie(name, path="/api/auth/google/callback")
    return response
