# dashboard-admin/backend/auth/models.py
import os
from typing import Dict
from pydantic import BaseModel

from security import get_password_hash

class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

# qui definisci il nostro unico admin, password da ENV o default "admin"
_ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin")
fake_users_db: Dict[str, UserInDB] = {
    "admin": UserInDB(
        username="admin",
        hashed_password=get_password_hash(_ADMIN_PASS)
    )
}
