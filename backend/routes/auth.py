import os
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, Header, HTTPException, Request
from jose import jwt
from passlib.context import CryptContext

from backend.database import database
from backend.models.users import EmailLoginRequest, LoginRequest, UserCreate
from backend.models.documents import utc_now

router = APIRouter(prefix="/api/businesses/{business_id}/users", tags=["authentication"])
platform_router = APIRouter(prefix="/api/platform", tags=["super admin"])
login_router = APIRouter(prefix="/api/auth", tags=["authentication"])
passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")


def check_business(business_id):
    if not ObjectId.is_valid(business_id) or not database.businesses.find_one({"_id": ObjectId(business_id)}):
        raise HTTPException(status_code=404, detail="Business not found")


@router.post("", status_code=201)
def create_user(business_id: str, payload: UserCreate, request: Request, authorization: str | None = Header(default=None)):
    check_business(business_id)
    existing_users = database.users.count_documents({"business_id": business_id})
    if existing_users == 0:
        if request.client.host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
            raise HTTPException(status_code=403, detail="Initial setup is available only from this computer")
    else:
        secret = os.getenv("JWT_SECRET")
        try:
            scheme, token = (authorization or "").split(" ", 1)
            claims = jwt.decode(token, secret, algorithms=["HS256"]) if scheme.lower() == "bearer" and secret else {}
        except Exception:
            claims = {}
        if claims.get("business_id") != business_id or claims.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only a signed-in business admin can add users")
    if payload.role not in {"admin", "cashier", "manager"}:
        raise HTTPException(status_code=400, detail="Unsupported role")
    if database.users.find_one({"business_id": business_id, "email": payload.email}):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = {"business_id": business_id, "email": payload.email, "password_hash": passwords.hash(payload.password), "role": payload.role, "created_at": utc_now()}
    result = database.users.insert_one(user)
    return {"id": str(result.inserted_id), "email": payload.email, "role": payload.role}


@router.post("/login")
def login(business_id: str, payload: LoginRequest):
    check_business(business_id)
    user = next((candidate for candidate in database.users.find({"business_id": business_id}) if passwords.verify(payload.password, candidate["password_hash"])), None)
    if not user:
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Set JWT_SECRET in the environment before signing in")
    expires = datetime.now(timezone.utc) + timedelta(hours=8)
    token = jwt.encode({"sub": str(user["_id"]), "business_id": business_id, "role": user["role"], "exp": expires}, secret, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "expires_at": expires}


@login_router.post("/login")
def login_with_email(payload: EmailLoginRequest):
    user = database.users.find_one({"email": payload.email})
    if not user or not passwords.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Set JWT_SECRET in the environment before signing in")
    expires = datetime.now(timezone.utc) + timedelta(hours=8)
    token = jwt.encode({"sub": str(user["_id"]), "business_id": user.get("business_id"), "role": user["role"], "exp": expires}, secret, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "business_id": user.get("business_id"), "expires_at": expires}


@platform_router.post("/setup-admin", status_code=201)
def setup_super_admin(payload: UserCreate, request: Request):
    if request.client.host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
        raise HTTPException(status_code=403, detail="Initial setup is available only from this computer")
    if database.users.count_documents({"role": "super_admin"}):
        raise HTTPException(status_code=403, detail="A platform admin already exists")
    if database.users.find_one({"email": payload.email}):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = {"business_id": None, "email": payload.email, "password_hash": passwords.hash(payload.password), "role": "super_admin", "created_at": utc_now()}
    result = database.users.insert_one(user)
    return {"id": str(result.inserted_id), "email": payload.email, "role": "super_admin"}


@platform_router.post("/login")
def platform_login(payload: LoginRequest):
    user = database.users.find_one({"email": payload.email, "role": "super_admin"})
    if not user or not passwords.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Set JWT_SECRET before signing in")
    expires = datetime.now(timezone.utc) + timedelta(hours=8)
    token = jwt.encode({"sub": str(user["_id"]), "business_id": None, "role": "super_admin", "exp": expires}, secret, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "expires_at": expires}
