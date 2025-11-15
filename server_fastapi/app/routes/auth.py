from fastapi import APIRouter, Depends, HTTPException, Response, Request
from app.db import mongo
from app.schemas.user import UserCreate, UserOut, LoginRequest
from app.utils.hash import hash_password, verify_password
from app.auth.jwt import create_access_token, verify_token
from bson import ObjectId

router = APIRouter()

COOKIE_OPTIONS = {
    "httponly": True,
    "samesite": "lax",
    "secure": False,
}


def serialize_user(user: dict) -> dict:
    return {
        "_id": str(user.get("_id")),
        "id": str(user.get("_id")),
        "name": user.get("name"),
        "email": user.get("email"),
        "credits": user.get("credits", 100),
    }


@router.post("/google")
async def google_auth(payload: dict, response: Response):
    name = payload.get("name")
    email = payload.get("email")
    if not name or not email:
        raise HTTPException(status_code=400, detail="Name and email are required")

    user = await mongo.db.users.find_one({"email": email})
    if not user:
        result = await mongo.db.users.insert_one({"name": name, "email": email, "credits": 100})
        user = {"_id": result.inserted_id, "name": name, "email": email, "credits": 100}

    token = create_access_token({"user_id": str(user.get("_id")), "email": user.get("email")})
    response.set_cookie(key="token", value=token, **COOKIE_OPTIONS)

    return serialize_user(user)


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    existing = await mongo.db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user.password)
    doc = {"name": user.name, "email": user.email, "password": hashed, "credits": 100}
    res = await mongo.db.users.insert_one(doc)
    return {"id": str(res.inserted_id), "name": user.name, "email": user.email, "credits": 100}


@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    user = await mongo.db.users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user.get("password")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"user_id": str(user.get("_id")), "email": user.get("email")})
    # use cookie name `token` to match original project
    response.set_cookie(key="token", value=token, **COOKIE_OPTIONS)
    return {"message": "logged in"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("token")
    return {"message": "logged out"}


@router.get("/logout")
async def logout_get(response: Response):
    response.delete_cookie("token")
    return {"message": "logged out"}


async def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    data = verify_token(token)
    user_id = data.get("user_id")
    user = await mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return serialize_user(user)
