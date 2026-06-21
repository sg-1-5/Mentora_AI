from fastapi import APIRouter, Depends
from app.routes.auth import get_current_user

router = APIRouter()


@router.get("/profile")
async def profile(current_user=Depends(get_current_user)):
    return current_user


@router.get("/current-user")
async def current_user(current_user=Depends(get_current_user)):
    return current_user
