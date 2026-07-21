import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import httpx
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, UserOut, UserUpdate, Token

router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret or len(jwt_secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": expire, "iss": "ai-regulatory-compliance", "aud": "compliance-api"}, jwt_secret, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if os.getenv("AUTH_MODE", "local") == "oidc":
            issuer, audience, jwks_url = os.getenv("OIDC_ISSUER"), os.getenv("OIDC_AUDIENCE"), os.getenv("OIDC_JWKS_URL")
            if not issuer or not audience or not jwks_url:
                raise credentials_exception
            header = jwt.get_unverified_header(credentials.credentials)
            if header.get("alg") != "RS256":
                raise credentials_exception
            jwks = httpx.get(jwks_url, timeout=5.0).json().get("keys", [])
            key = next((item for item in jwks if item.get("kid") == header.get("kid")), None)
            if not key:
                raise credentials_exception
            signing_key = jwt.PyJWK.from_dict(key).key
            payload = jwt.decode(credentials.credentials, signing_key, algorithms=[header.get("alg", "RS256")], audience=audience, issuer=issuer)
            subject, email = payload.get("sub"), payload.get("email")
            if not subject or not email or payload.get("email_verified") is not True:
                raise credentials_exception
            user = db.query(User).filter(or_(User.oidc_subject == subject, User.email == email.lower())).first()
            if user and not user.oidc_subject:
                user.oidc_subject = subject
                db.commit()
        else:
            jwt_secret = os.getenv("JWT_SECRET")
            if not jwt_secret or len(jwt_secret) < 32:
                raise credentials_exception
            payload = jwt.decode(credentials.credentials, jwt_secret, algorithms=[JWT_ALGORITHM], audience="compliance-api", issuer="ai-regulatory-compliance")
            user_id: Optional[str] = payload.get("sub")
            if not user_id:
                raise credentials_exception
            user = db.query(User).filter(User.id == user_id).first()
    except (jwt.PyJWTError, httpx.HTTPError, ValueError, StopIteration):
        raise credentials_exception

    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    if os.getenv("AUTH_MODE", "local") == "oidc" or os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Local registration is disabled; use the configured identity provider")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    tenant_id = f"tenant_{uuid.uuid4().hex}"
    db.execute(text("INSERT INTO tenants(id, name) VALUES (:id, :name)"), {"id": tenant_id, "name": payload.organization.strip()})
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), name=payload.name,
                organization=payload.organization.strip(), role="admin", tenant_id=tenant_id)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
@limiter.limit("20/hour")
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    if os.getenv("AUTH_MODE", "local") == "oidc" or os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=403, detail="Local login is disabled; use the configured identity provider")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.name is not None:
        current_user.name = payload.name
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Client-side logout: instruct the client to discard the token.
    For server-side invalidation, implement a token denylist (e.g. Redis).
    """
    return {"message": "Logged out successfully. Please discard your token."}


@router.post("/users", status_code=status.HTTP_201_CREATED)
def provision_user(payload: dict, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    email, name, role = str(payload.get("email", "")).lower(), str(payload.get("name", "")).strip(), payload.get("role", "viewer")
    if role not in {"admin", "analyst", "viewer"} or not email or not name:
        raise HTTPException(status_code=400, detail="Valid email, name, and role are required")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    if os.getenv("AUTH_MODE", "local") == "oidc":
        password_hash = "OIDC_ONLY"
    else:
        password = str(payload.get("password", ""))
        if len(password) < 12:
            raise HTTPException(status_code=400, detail="A 12+ character temporary password is required")
        password_hash = hash_password(password)
    user = User(email=email, name=name, role=role, password_hash=password_hash, tenant_id=current_user.tenant_id,
                organization=current_user.organization, oidc_subject=payload.get("oidc_subject"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/users")
def list_tenant_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.tenant_id == current_user.tenant_id, User.is_active.is_(True)).order_by(User.name).all()
    return [UserOut.model_validate(user) for user in users]
