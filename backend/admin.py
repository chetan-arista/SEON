"""Administrator-only user and account management routes."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend import storage

router = APIRouter(prefix="/api/admin", tags=["administration"])


class RoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|company|client)$")


class AccountState(BaseModel):
    disabled: bool


@router.get("/users")
async def users() -> dict:
    return {"users": storage.list_users()}


@router.patch("/users/{user_id}/role")
async def update_role(user_id: str, body: RoleUpdate, request: Request) -> dict:
    current = request.state.user
    if current["id"] == user_id and body.role != "admin":
        raise HTTPException(400, "You cannot remove your own administrator access.")
    try:
        if not storage.set_user_role(user_id, body.role):
            raise HTTPException(404, "Account not found.")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    return {"ok": True, "user_id": user_id, "role": body.role}


@router.patch("/users/{user_id}/state")
async def update_state(user_id: str, body: AccountState, request: Request) -> dict:
    if request.state.user["id"] == user_id and body.disabled:
        raise HTTPException(400, "You cannot disable your own administrator account.")
    try:
        if not storage.set_user_disabled(user_id, body.disabled):
            raise HTTPException(404, "Account not found.")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    return {"ok": True, "user_id": user_id, "disabled": body.disabled}
