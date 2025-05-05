# dashboard-admin/backend/auth/security.py
import os
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt

# carica da .env (docker-compose.env_file)
JWT_SECRET       = os.getenv("JWT_SECRET", "secret")
JWT_ALGORITHM    = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_S = int(os.getenv("JWT_EXPIRATION_S", "3600"))
ADMIN_PASSWORD   = os.getenv("ADMIN_PASSWORD", "admin")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(
    *,
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION_S)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt
